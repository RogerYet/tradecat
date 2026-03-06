package market

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"time"
)

const (
	binanceFuturesKlinesURL = "https://fapi.binance.com/fapi/v1/klines"
	binanceMaxKlineLimit    = 1500
)

// GetKlinesRange fetches K-line series within specified time range (closed interval), returns data sorted by time in ascending order.
func GetKlinesRange(symbol string, timeframe string, start, end time.Time) ([]Kline, error) {
	symbol = Normalize(symbol)
	normTF, err := NormalizeTimeframe(timeframe)
	if err != nil {
		return nil, err
	}
	if !end.After(start) {
		return nil, fmt.Errorf("end time must be after start time")
	}

	if usingAIPayloadSource() {
		if klines, ok := getKlinesRangeFromAIPayload(symbol, normTF, start, end); ok {
			return klines, nil
		}
	}

	if usingTradecatSource() {
		return getKlinesRangeFromTradecat(symbol, normTF, start, end)
	}

	startMs := start.UnixMilli()
	endMs := end.UnixMilli()

	var all []Kline
	cursor := startMs

	client := &http.Client{Timeout: 15 * time.Second}

	for cursor < endMs {
		req, err := http.NewRequest("GET", binanceFuturesKlinesURL, nil)
		if err != nil {
			return nil, err
		}

		q := req.URL.Query()
		q.Set("symbol", symbol)
		q.Set("interval", normTF)
		q.Set("limit", fmt.Sprintf("%d", binanceMaxKlineLimit))
		q.Set("startTime", fmt.Sprintf("%d", cursor))
		q.Set("endTime", fmt.Sprintf("%d", endMs))
		req.URL.RawQuery = q.Encode()

		resp, err := client.Do(req)
		if err != nil {
			return nil, err
		}

		body, err := io.ReadAll(resp.Body)
		resp.Body.Close()
		if err != nil {
			return nil, err
		}
		if resp.StatusCode != http.StatusOK {
			return nil, fmt.Errorf("binance klines api returned status %d: %s", resp.StatusCode, string(body))
		}

		var raw [][]interface{}
		if err := json.Unmarshal(body, &raw); err != nil {
			return nil, err
		}
		if len(raw) == 0 {
			break
		}

		batch := make([]Kline, len(raw))
		for i, item := range raw {
			openTime := int64(item[0].(float64))
			open, _ := parseFloat(item[1])
			high, _ := parseFloat(item[2])
			low, _ := parseFloat(item[3])
			close, _ := parseFloat(item[4])
			volume, _ := parseFloat(item[5])
			closeTime := int64(item[6].(float64))

			batch[i] = Kline{
				OpenTime:  openTime,
				Open:      open,
				High:      high,
				Low:       low,
				Close:     close,
				Volume:    volume,
				CloseTime: closeTime,
			}
		}

		all = append(all, batch...)

		last := batch[len(batch)-1]
		cursor = last.CloseTime + 1

		// If returned quantity is less than request limit, reached the end, can exit early.
		if len(batch) < binanceMaxKlineLimit {
			break
		}
	}

	return all, nil
}

func getKlinesRangeFromAIPayload(symbol string, timeframe string, start, end time.Time) ([]Kline, bool) {
	payload, err := loadAIPayload(symbol)
	if err != nil {
		return nil, false
	}

	var klines []Kline
	if timeframe == "3m" {
		base := payload.Candles["1m"]
		if len(base) == 0 {
			return nil, false
		}
		source := buildKlinesFromAICandles(base)
		klines = aggregateKlines(source, 3)
	} else {
		rows := payload.Candles[timeframe]
		if len(rows) == 0 {
			return nil, false
		}
		klines = buildKlinesFromAICandles(rows)
	}

	if len(klines) == 0 {
		return nil, false
	}

	startMs := start.UnixMilli()
	endMs := end.UnixMilli()
	var filtered []Kline
	for _, k := range klines {
		if k.OpenTime >= startMs && k.OpenTime <= endMs {
			filtered = append(filtered, k)
		}
	}

	if len(filtered) == 0 {
		return nil, false
	}

	return filtered, true
}

func getKlinesRangeFromTradecat(symbol string, timeframe string, start, end time.Time) ([]Kline, error) {
	startMs := start.UnixMilli()
	endMs := end.UnixMilli()
	if endMs <= startMs {
		return nil, fmt.Errorf("end time must be after start time")
	}

	var all []Kline
	cursor := startMs
	limit := 1000

	client := &http.Client{Timeout: 15 * time.Second}

	for cursor < endMs {
		req, err := http.NewRequest("GET", tradecatURL("/ohlc/history"), nil)
		if err != nil {
			return nil, err
		}

		q := req.URL.Query()
		q.Set("symbol", symbol)
		q.Set("exchange", "binance_futures_um")
		q.Set("interval", timeframe)
		q.Set("limit", strconv.Itoa(limit))
		q.Set("startTime", fmt.Sprintf("%d", cursor))
		q.Set("endTime", fmt.Sprintf("%d", endMs))
		req.URL.RawQuery = q.Encode()

		resp, err := client.Do(req)
		if err != nil {
			return nil, err
		}

		body, err := io.ReadAll(resp.Body)
		resp.Body.Close()
		if err != nil {
			return nil, err
		}
		if resp.StatusCode != http.StatusOK {
			return nil, fmt.Errorf("tradecat ohlc api returned status %d: %s", resp.StatusCode, string(body))
		}

		var result tradecatOHLCResponse
		if err := json.Unmarshal(body, &result); err != nil {
			return nil, err
		}
		if !result.Success {
			return nil, fmt.Errorf("tradecat ohlc api failed: %s", result.Msg)
		}
		if len(result.Data) == 0 {
			break
		}

		batch := make([]Kline, 0, len(result.Data))
		for _, item := range result.Data {
			batch = append(batch, Kline{
				OpenTime:            item.Time,
				Open:                parseFloatString(item.Open),
				High:                parseFloatString(item.High),
				Low:                 parseFloatString(item.Low),
				Close:               parseFloatString(item.Close),
				Volume:              parseFloatString(item.Volume),
				CloseTime:           item.Time,
				QuoteVolume:         parseFloatString(item.VolumeUSD),
				Trades:              0,
				TakerBuyBaseVolume:  0,
				TakerBuyQuoteVolume: 0,
			})
		}

		all = append(all, batch...)
		last := batch[len(batch)-1]
		if last.OpenTime <= cursor {
			break
		}
		cursor = last.OpenTime + 1

		if len(batch) < limit {
			break
		}
	}

	return all, nil
}
