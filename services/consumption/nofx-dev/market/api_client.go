package market

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"nofx/hook"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

const (
	binanceBaseURL        = "https://fapi.binance.com"
	tradecatDefaultBaseURL = "http://127.0.0.1:8088/api/futures"
)

type APIClient struct {
	client *http.Client
}

type aiPayload struct {
	Symbol  string                 `json:"symbol"`
	Interval string                `json:"interval"`
	Candles map[string][]aiCandle  `json:"candles"`
	Metrics []aiMetric             `json:"metrics"`
}

type aiCandle struct {
	BucketTS            string  `json:"bucket_ts"`
	Open                float64 `json:"open"`
	High                float64 `json:"high"`
	Low                 float64 `json:"low"`
	Close               float64 `json:"close"`
	Volume              float64 `json:"volume"`
	QuoteVolume         float64 `json:"quote_volume"`
	TradeCount          float64 `json:"trade_count"`
	TakerBuyVolume      float64 `json:"taker_buy_volume"`
	TakerBuyQuoteVolume float64 `json:"taker_buy_quote_volume"`
}

type aiMetric struct {
	CreateTime              string `json:"create_time"`
	SumOpenInterest         string `json:"sum_open_interest"`
	SumOpenInterestValue    string `json:"sum_open_interest_value"`
	SumTopTraderLongShort   string `json:"sum_toptrader_long_short_ratio"`
	SumTakerLongShortVol    string `json:"sum_taker_long_short_vol_ratio"`
}

type tradecatCoinsResponse struct {
	Code    string   `json:"code"`
	Msg     string   `json:"msg"`
	Data    []string `json:"data"`
	Success bool     `json:"success"`
}

type tradecatOHLCItem struct {
	Time      int64  `json:"time"`
	Open      string `json:"open"`
	High      string `json:"high"`
	Low       string `json:"low"`
	Close     string `json:"close"`
	Volume    string `json:"volume"`
	VolumeUSD string `json:"volume_usd"`
}

type tradecatOHLCResponse struct {
	Code    string            `json:"code"`
	Msg     string            `json:"msg"`
	Data    []tradecatOHLCItem `json:"data"`
	Success bool              `json:"success"`
}

func NewAPIClient() *APIClient {
	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	hookRes := hook.HookExec[hook.SetHttpClientResult](hook.SET_HTTP_CLIENT, client)
	if hookRes != nil && hookRes.Error() == nil {
		log.Printf("Using HTTP client set by Hook")
		client = hookRes.GetResult()
	}

	return &APIClient{
		client: client,
	}
}

func marketDataSource() string {
	if v := strings.TrimSpace(os.Getenv("NOFX_MARKET_DATA_SOURCE")); v != "" {
		return strings.ToLower(v)
	}
	if v := strings.TrimSpace(os.Getenv("NOFX_MARKET_API_BASE_URL")); v != "" {
		return "tradecat"
	}
	return "binance"
}

func usingTradecatSource() bool {
	return marketDataSource() == "tradecat"
}

func usingAIPayloadSource() bool {
	switch marketDataSource() {
	case "ai", "ai_service", "ai_payload":
		return true
	default:
		return false
	}
}

// UsingAIPayloadSource exposes ai payload source status for other packages.
func UsingAIPayloadSource() bool {
	return usingAIPayloadSource()
}

// ListAIPayloadSymbols lists symbols found under ai-service data directory.
func ListAIPayloadSymbols() ([]string, error) {
	root, err := resolveAIPayloadDir()
	if err != nil {
		return nil, err
	}

	entries, err := os.ReadDir(root)
	if err != nil {
		return nil, err
	}

	symbolsMap := make(map[string]struct{})
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		name := entry.Name()
		symbol := extractSymbolFromPayloadDir(name)
		if symbol == "" {
			continue
		}
		symbolsMap[symbol] = struct{}{}
	}

	if len(symbolsMap) == 0 {
		return nil, fmt.Errorf("ai payload symbols not found")
	}

	symbols := make([]string, 0, len(symbolsMap))
	for sym := range symbolsMap {
		symbols = append(symbols, sym)
	}
	sort.Strings(symbols)
	return symbols, nil
}

func marketAPIBaseURL() string {
	if usingTradecatSource() {
		if v := strings.TrimSpace(os.Getenv("NOFX_MARKET_API_BASE_URL")); v != "" {
			return strings.TrimRight(v, "/")
		}
		return tradecatDefaultBaseURL
	}
	return binanceBaseURL
}

func tradecatURL(path string) string {
	base := strings.TrimRight(marketAPIBaseURL(), "/")
	return base + path
}

func (c *APIClient) GetExchangeInfo() (*ExchangeInfo, error) {
	if usingAIPayloadSource() {
		return c.getAIPayloadExchangeInfo()
	}
	if usingTradecatSource() {
		return c.getTradecatExchangeInfo()
	}

	url := fmt.Sprintf("%s/fapi/v1/exchangeInfo", binanceBaseURL)
	resp, err := c.client.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	var exchangeInfo ExchangeInfo
	err = json.Unmarshal(body, &exchangeInfo)
	if err != nil {
		return nil, err
	}

	return &exchangeInfo, nil
}

func (c *APIClient) GetKlines(symbol, interval string, limit int) ([]Kline, error) {
	if usingAIPayloadSource() {
		klines, err := c.getAIPayloadKlines(symbol, interval, limit)
		if err == nil && len(klines) > 0 {
			return klines, nil
		}
	}
	if usingTradecatSource() {
		return c.getTradecatKlines(symbol, interval, limit)
	}

	url := fmt.Sprintf("%s/fapi/v1/klines", binanceBaseURL)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	q := req.URL.Query()
	q.Add("symbol", symbol)
	q.Add("interval", interval)
	q.Add("limit", strconv.Itoa(limit))
	req.URL.RawQuery = q.Encode()

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var klineResponses []KlineResponse
	err = json.Unmarshal(body, &klineResponses)
	if err != nil {
		log.Printf("Failed to get K-line data, response content: %s", string(body))
		return nil, err
	}

	var klines []Kline
	for _, kr := range klineResponses {
		kline, err := parseKline(kr)
		if err != nil {
			log.Printf("Failed to parse K-line data: %v", err)
			continue
		}
		klines = append(klines, kline)
	}

	return klines, nil
}

func parseKline(kr KlineResponse) (Kline, error) {
	var kline Kline

	if len(kr) < 11 {
		return kline, fmt.Errorf("invalid kline data")
	}

	// Parse each field
	kline.OpenTime = int64(kr[0].(float64))
	kline.Open, _ = strconv.ParseFloat(kr[1].(string), 64)
	kline.High, _ = strconv.ParseFloat(kr[2].(string), 64)
	kline.Low, _ = strconv.ParseFloat(kr[3].(string), 64)
	kline.Close, _ = strconv.ParseFloat(kr[4].(string), 64)
	kline.Volume, _ = strconv.ParseFloat(kr[5].(string), 64)
	kline.CloseTime = int64(kr[6].(float64))
	kline.QuoteVolume, _ = strconv.ParseFloat(kr[7].(string), 64)
	kline.Trades = int(kr[8].(float64))
	kline.TakerBuyBaseVolume, _ = strconv.ParseFloat(kr[9].(string), 64)
	kline.TakerBuyQuoteVolume, _ = strconv.ParseFloat(kr[10].(string), 64)

	return kline, nil
}

func (c *APIClient) GetCurrentPrice(symbol string) (float64, error) {
	if usingAIPayloadSource() {
		klines, err := c.getAIPayloadKlines(symbol, "1m", 1)
		if err == nil && len(klines) > 0 {
			return klines[len(klines)-1].Close, nil
		}
	}
	if usingTradecatSource() {
		klines, err := c.getTradecatKlines(symbol, "1m", 1)
		if err != nil {
			return 0, err
		}
		if len(klines) == 0 {
			return 0, fmt.Errorf("tradecat price data is empty")
		}
		return klines[len(klines)-1].Close, nil
	}

	url := fmt.Sprintf("%s/fapi/v1/ticker/price", binanceBaseURL)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return 0, err
	}

	q := req.URL.Query()
	q.Add("symbol", symbol)
	req.URL.RawQuery = q.Encode()

	resp, err := c.client.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return 0, err
	}

	var ticker PriceTicker
	err = json.Unmarshal(body, &ticker)
	if err != nil {
		return 0, err
	}

	price, err := strconv.ParseFloat(ticker.Price, 64)
	if err != nil {
		return 0, err
	}

	return price, nil
}

func (c *APIClient) getTradecatExchangeInfo() (*ExchangeInfo, error) {
	url := tradecatURL("/supported-coins")
	resp, err := c.client.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result tradecatCoinsResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, err
	}
	if !result.Success {
		return nil, fmt.Errorf("tradecat coins api failed: %s", result.Msg)
	}

	symbols := make([]SymbolInfo, 0, len(result.Data))
	for _, base := range result.Data {
		sym := strings.ToUpper(strings.TrimSpace(base))
		if sym == "" {
			continue
		}
		if !strings.HasSuffix(sym, "USDT") {
			sym += "USDT"
		}
		symbols = append(symbols, SymbolInfo{
			Symbol:       sym,
			Status:       "TRADING",
			ContractType: "PERPETUAL",
		})
	}

	return &ExchangeInfo{Symbols: symbols}, nil
}

func (c *APIClient) getTradecatKlines(symbol, interval string, limit int) ([]Kline, error) {
	url := tradecatURL("/ohlc/history")
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	q := req.URL.Query()
	q.Add("symbol", symbol)
	q.Add("exchange", "binance_futures_um")
	q.Add("interval", interval)
	q.Add("limit", strconv.Itoa(limit))
	req.URL.RawQuery = q.Encode()

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result tradecatOHLCResponse
	if err := json.Unmarshal(body, &result); err != nil {
		log.Printf("Failed to parse TradeCat OHLC response: %s", string(body))
		return nil, err
	}
	if !result.Success {
		return nil, fmt.Errorf("tradecat ohlc api failed: %s", result.Msg)
	}

	klines := make([]Kline, 0, len(result.Data))
	for _, item := range result.Data {
		open := parseFloatString(item.Open)
		high := parseFloatString(item.High)
		low := parseFloatString(item.Low)
		closePrice := parseFloatString(item.Close)
		volume := parseFloatString(item.Volume)
		quoteVolume := parseFloatString(item.VolumeUSD)
		klines = append(klines, Kline{
			OpenTime:            item.Time,
			Open:                open,
			High:                high,
			Low:                 low,
			Close:               closePrice,
			Volume:              volume,
			CloseTime:           item.Time,
			QuoteVolume:         quoteVolume,
			Trades:              0,
			TakerBuyBaseVolume:  0,
			TakerBuyQuoteVolume: 0,
		})
	}

	return klines, nil
}

func (c *APIClient) getAIPayloadExchangeInfo() (*ExchangeInfo, error) {
	root, err := resolveAIPayloadDir()
	if err != nil {
		return nil, err
	}

	entries, err := os.ReadDir(root)
	if err != nil {
		return nil, err
	}

	symbolsMap := make(map[string]struct{})
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		name := entry.Name()
		idx := strings.Index(name, "_")
		if idx <= 0 {
			continue
		}
		sym := strings.ToUpper(strings.TrimSpace(name[:idx]))
		if sym == "" {
			continue
		}
		if !strings.HasSuffix(sym, "USDT") {
			sym += "USDT"
		}
		symbolsMap[sym] = struct{}{}
	}

	if len(symbolsMap) == 0 {
		return nil, fmt.Errorf("ai payload symbols not found")
	}

	symbols := make([]SymbolInfo, 0, len(symbolsMap))
	for sym := range symbolsMap {
		symbols = append(symbols, SymbolInfo{
			Symbol:       sym,
			Status:       "TRADING",
			ContractType: "PERPETUAL",
		})
	}

	return &ExchangeInfo{Symbols: symbols}, nil
}

func (c *APIClient) getAIPayloadKlines(symbol, interval string, limit int) ([]Kline, error) {
	payload, err := loadAIPayload(symbol)
	if err != nil {
		return nil, err
	}

	if interval == "3m" {
		base := payload.Candles["1m"]
		if len(base) == 0 {
			return nil, fmt.Errorf("ai payload missing 1m candles")
		}
		source := buildKlinesFromAICandles(base)
		klines := aggregateKlines(source, 3)
		return trimKlines(klines, limit), nil
	}

	rows, ok := payload.Candles[interval]
	if !ok || len(rows) == 0 {
		return nil, fmt.Errorf("ai payload missing %s candles", interval)
	}

	klines := buildKlinesFromAICandles(rows)
	return trimKlines(klines, limit), nil
}

func resolveAIPayloadDir() (string, error) {
	if v := strings.TrimSpace(os.Getenv("NOFX_AI_PAYLOAD_DIR")); v != "" {
		if dirExists(v) {
			return v, nil
		}
	}

	wd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("无法获取工作目录")
	}

	dir := wd
	for i := 0; i < 8; i++ {
		candidate := filepath.Join(dir, "services", "ai-service", "data", "ai")
		if dirExists(candidate) {
			return candidate, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}

	return "", fmt.Errorf("未找到 ai-service data 目录")
}

func dirExists(path string) bool {
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	return info.IsDir()
}

func loadAIPayload(symbol string) (*aiPayload, error) {
	root, err := resolveAIPayloadDir()
	if err != nil {
		return nil, err
	}

	target, err := findLatestPayloadDir(root, symbol)
	if err != nil {
		return nil, err
	}

	payloadPath := filepath.Join(target, "raw_payload.json")
	raw, err := os.ReadFile(payloadPath)
	if err != nil {
		return nil, err
	}

	var payload aiPayload
	if err := json.Unmarshal(raw, &payload); err != nil {
		return nil, err
	}
	if payload.Symbol == "" {
		payload.Symbol = strings.ToUpper(symbol)
	}
	return &payload, nil
}

// LoadAIPayloadRaw loads raw_payload.json into a generic map without field loss.
func LoadAIPayloadRaw(symbol string) (map[string]any, error) {
	root, err := resolveAIPayloadDir()
	if err != nil {
		return nil, err
	}

	target, err := findLatestPayloadDir(root, symbol)
	if err != nil {
		return nil, err
	}

	payloadPath := filepath.Join(target, "raw_payload.json")
	raw, err := os.ReadFile(payloadPath)
	if err != nil {
		return nil, err
	}

	var payload map[string]any
	if err := json.Unmarshal(raw, &payload); err != nil {
		return nil, err
	}
	if _, ok := payload["symbol"]; !ok || payload["symbol"] == "" {
		payload["symbol"] = strings.ToUpper(symbol)
	}
	return payload, nil
}

func findLatestPayloadDir(root, symbol string) (string, error) {
	entries, err := os.ReadDir(root)
	if err != nil {
		return "", err
	}

	prefix := strings.ToUpper(symbol) + "_"
	latest := ""
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		name := entry.Name()
		if !strings.HasPrefix(strings.ToUpper(name), prefix) {
			continue
		}
		if name > latest {
			latest = name
		}
	}
	if latest == "" {
		return "", fmt.Errorf("未找到 %s 的 ai payload", symbol)
	}

	return filepath.Join(root, latest), nil
}

func extractSymbolFromPayloadDir(name string) string {
	parts := strings.Split(name, "_")
	if len(parts) < 3 {
		return ""
	}
	symbol := strings.Join(parts[:len(parts)-2], "_")
	return strings.ToUpper(symbol)
}

func buildKlinesFromAICandles(rows []aiCandle) []Kline {
	klines := make([]Kline, 0, len(rows))
	for i := len(rows) - 1; i >= 0; i-- {
		row := rows[i]
		ts := parseBucketTime(row.BucketTS)
		if ts == 0 {
			continue
		}
		klines = append(klines, Kline{
			OpenTime:            ts,
			Open:                row.Open,
			High:                row.High,
			Low:                 row.Low,
			Close:               row.Close,
			Volume:              row.Volume,
			CloseTime:           ts,
			QuoteVolume:         row.QuoteVolume,
			Trades:              int(row.TradeCount),
			TakerBuyBaseVolume:  row.TakerBuyVolume,
			TakerBuyQuoteVolume: row.TakerBuyQuoteVolume,
		})
	}
	return klines
}

func parseBucketTime(raw string) int64 {
	if raw == "" {
		return 0
	}
	layouts := []string{
		"2006-01-02 15:04:05-07:00",
		"2006-01-02 15:04:05Z07:00",
		"2006-01-02T15:04:05Z07:00",
	}
	for _, layout := range layouts {
		if t, err := time.Parse(layout, raw); err == nil {
			return t.UnixMilli()
		}
	}
	return 0
}

func aggregateKlines(input []Kline, bucketMinutes int64) []Kline {
	if len(input) == 0 {
		return nil
	}
	bucketMs := bucketMinutes * 60 * 1000
	var result []Kline

	var current *Kline
	var currentBucket int64

	for _, k := range input {
		bucket := (k.OpenTime / bucketMs) * bucketMs
		if current == nil || bucket != currentBucket {
			if current != nil {
				result = append(result, *current)
			}
			currentBucket = bucket
			current = &Kline{
				OpenTime:            bucket,
				Open:                k.Open,
				High:                k.High,
				Low:                 k.Low,
				Close:               k.Close,
				Volume:              k.Volume,
				CloseTime:           k.CloseTime,
				QuoteVolume:         k.QuoteVolume,
				Trades:              k.Trades,
				TakerBuyBaseVolume:  k.TakerBuyBaseVolume,
				TakerBuyQuoteVolume: k.TakerBuyQuoteVolume,
			}
			continue
		}

		if k.High > current.High {
			current.High = k.High
		}
		if current.Low == 0 || k.Low < current.Low {
			current.Low = k.Low
		}
		current.Close = k.Close
		current.Volume += k.Volume
		current.QuoteVolume += k.QuoteVolume
		current.Trades += k.Trades
		current.TakerBuyBaseVolume += k.TakerBuyBaseVolume
		current.TakerBuyQuoteVolume += k.TakerBuyQuoteVolume
		current.CloseTime = k.CloseTime
	}

	if current != nil {
		result = append(result, *current)
	}
	return result
}

func trimKlines(klines []Kline, limit int) []Kline {
	if limit <= 0 || len(klines) <= limit {
		return klines
	}
	return klines[len(klines)-limit:]
}

func parseFloatString(raw string) float64 {
	if raw == "" {
		return 0
	}
	v, err := strconv.ParseFloat(raw, 64)
	if err != nil {
		return 0
	}
	return v
}
