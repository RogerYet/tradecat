package provider

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"nofx/logger"
	"regexp"
	"sort"
	"strings"
	"time"
)

// PolymarketMarket represents a single prediction market
type PolymarketMarket struct {
	Question        string  `json:"question"`
	OutcomePrices   string  `json:"outcomePrices"` // JSON string: ["0.85", "0.15"]
	Volume24hr      float64 `json:"volume24hr"`
	LiquidityNum    float64 `json:"liquidityNum"`
	OneDayPriceChange float64 `json:"oneDayPriceChange"`
	EndDate         string  `json:"endDate"`
}

// PolymarketSentiment represents sentiment data for a symbol
type PolymarketSentiment struct {
	Symbol       string
	Markets      []PolymarketParsedMarket
	TotalMarkets int
	TotalVolume  float64
	BullishAvg   float64 // Average YES probability for bullish predictions
	BearishAvg   float64 // Average YES probability for bearish predictions
}

// PolymarketParsedMarket represents a parsed market with YES/NO probabilities
type PolymarketParsedMarket struct {
	Question      string
	YesProbability float64
	NoProbability  float64
	Volume24hr    float64
	Liquidity     float64
	PriceChange24h float64
	EndDateBeijing string
}

// Symbol to search keywords mapping
var polymarketSymbolKeywords = map[string][]string{
	"BTCUSDT":  {"bitcoin", "btc"},
	"ETHUSDT":  {"ethereum"},
	"SOLUSDT":  {"solana"},
	"XRPUSDT":  {"xrp"},
	"DOGEUSDT": {"dogecoin", "doge"},
	"LINKUSDT": {"chainlink"},
	"UNIUSDT":  {"uniswap"},
}

// Exclude patterns for false positives
var polymarketExcludePatterns = []string{
	"netherlands", "fifa", "football", "soccer", "nfl", "nba",
	"manchester", "union saint", "seize", "russia", "ukraine", "kyiv",
}

// FetchPolymarketData fetches prediction market data for given symbols
func FetchPolymarketData(symbols []string) map[string]*PolymarketSentiment {
	result := make(map[string]*PolymarketSentiment)

	// Filter symbols that have Polymarket support
	supportedSymbols := []string{}
	for _, symbol := range symbols {
		if _, ok := polymarketSymbolKeywords[symbol]; ok {
			supportedSymbols = append(supportedSymbols, symbol)
		}
	}

	if len(supportedSymbols) == 0 {
		return result
	}

	// Fetch all markets once
	markets, err := fetchPolymarketMarkets(500)
	if err != nil {
		logger.Warnf("⚠️  Failed to fetch Polymarket data: %v", err)
		return result
	}

	// Process each supported symbol
	for _, symbol := range supportedSymbols {
		sentiment := processMarketsForSymbol(markets, symbol)
		if sentiment != nil && len(sentiment.Markets) > 0 {
			result[symbol] = sentiment
		}
	}

	logger.Infof("📊 Polymarket data ready: %d symbols", len(result))
	return result
}

func fetchPolymarketMarkets(limit int) ([]PolymarketMarket, error) {
	url := fmt.Sprintf("https://gamma-api.polymarket.com/markets?active=true&closed=false&order=volume24hr&ascending=false&limit=%d", limit)

	// Try with longer timeout
	client := &http.Client{Timeout: 30 * time.Second}
	
	resp, err := client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP status: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read body failed: %w", err)
	}

	var markets []PolymarketMarket
	if err := json.Unmarshal(body, &markets); err != nil {
		return nil, fmt.Errorf("JSON parse failed: %w", err)
	}

	return markets, nil
}

func processMarketsForSymbol(markets []PolymarketMarket, symbol string) *PolymarketSentiment {
	keywords, ok := polymarketSymbolKeywords[symbol]
	if !ok {
		return nil
	}

	// Build regex pattern
	pattern := strings.Join(keywords, "|")
	re := regexp.MustCompile("(?i)" + pattern)

	// Build exclude pattern
	excludePattern := strings.Join(polymarketExcludePatterns, "|")
	excludeRe := regexp.MustCompile("(?i)" + excludePattern)

	var matched []PolymarketParsedMarket
	var totalVolume float64
	var bullishSum, bullishCount float64
	var bearishSum, bearishCount float64

	for _, m := range markets {
		question := m.Question

		// Check if matches symbol keywords
		if !re.MatchString(question) {
			continue
		}

		// Exclude false positives
		if excludeRe.MatchString(question) {
			continue
		}

		// Filter: only keep markets settling within 7 days
		if m.EndDate != "" {
			endTime, err := time.Parse(time.RFC3339, m.EndDate)
			if err == nil {
				daysUntilSettlement := endTime.Sub(time.Now()).Hours() / 24
				if daysUntilSettlement > 7 || daysUntilSettlement < -1 {
					continue // Skip markets settling > 7 days or already settled
				}
			}
		}

		// Parse outcome prices
		var prices []string
		if err := json.Unmarshal([]byte(m.OutcomePrices), &prices); err != nil || len(prices) < 2 {
			continue
		}

		var yesProb, noProb float64
		fmt.Sscanf(prices[0], "%f", &yesProb)
		fmt.Sscanf(prices[1], "%f", &noProb)

		// Convert end date to Beijing time
		endDateBeijing := convertToBeijingTime(m.EndDate)

		parsed := PolymarketParsedMarket{
			Question:       question,
			YesProbability: yesProb * 100,
			NoProbability:  noProb * 100,
			Volume24hr:     m.Volume24hr,
			Liquidity:      m.LiquidityNum,
			PriceChange24h: m.OneDayPriceChange * 100,
			EndDateBeijing: endDateBeijing,
		}

		matched = append(matched, parsed)
		totalVolume += m.Volume24hr

		// Categorize bullish/bearish
		questionLower := strings.ToLower(question)
		if strings.Contains(questionLower, "reach") || strings.Contains(questionLower, "above") || strings.Contains(questionLower, "hit") {
			bullishSum += yesProb
			bullishCount++
		} else if strings.Contains(questionLower, "dip") || strings.Contains(questionLower, "below") || strings.Contains(questionLower, "fall") {
			bearishSum += yesProb
			bearishCount++
		}
	}

	if len(matched) == 0 {
		return nil
	}

	// Sort by volume
	sort.Slice(matched, func(i, j int) bool {
		return matched[i].Volume24hr > matched[j].Volume24hr
	})

	// Keep top 8
	if len(matched) > 8 {
		matched = matched[:8]
	}

	var bullishAvg, bearishAvg float64
	if bullishCount > 0 {
		bullishAvg = bullishSum / bullishCount * 100
	}
	if bearishCount > 0 {
		bearishAvg = bearishSum / bearishCount * 100
	}

	return &PolymarketSentiment{
		Symbol:       symbol,
		Markets:      matched,
		TotalMarkets: len(matched),
		TotalVolume:  totalVolume,
		BullishAvg:   bullishAvg,
		BearishAvg:   bearishAvg,
	}
}

func convertToBeijingTime(isoTime string) string {
	if isoTime == "" {
		return "TBD"
	}

	t, err := time.Parse(time.RFC3339, isoTime)
	if err != nil {
		// Try without timezone
		t, err = time.Parse("2006-01-02T15:04:05Z", isoTime)
		if err != nil {
			return "TBD"
		}
	}

	// Add 8 hours for Beijing time
	beijing := t.Add(8 * time.Hour)
	return beijing.Format("01-02 15:04")
}

// FormatPolymarketForAI formats Polymarket data for AI prompt
func FormatPolymarketForAI(data map[string]*PolymarketSentiment) string {
	if len(data) == 0 {
		return ""
	}

	var sb strings.Builder
	sb.WriteString("## 📊 Prediction Market Sentiment (Polymarket)\n\n")

	// Sort by symbol for consistent output
	symbols := make([]string, 0, len(data))
	for symbol := range data {
		symbols = append(symbols, symbol)
	}
	sort.Strings(symbols)

	for _, symbol := range symbols {
		sentiment := data[symbol]
		sb.WriteString(fmt.Sprintf("### %s\n", symbol))
		sb.WriteString(fmt.Sprintf("Markets: %d | 24h Volume: $%.0fK | Bullish Avg: %.1f%% | Bearish Avg: %.1f%%\n\n",
			sentiment.TotalMarkets,
			sentiment.TotalVolume/1000,
			sentiment.BullishAvg,
			sentiment.BearishAvg))

		sb.WriteString("| Prediction | YES | NO | 24h Volume | Liquidity | Settlement (Beijing) |\n")
		sb.WriteString("|------------|-----|-----|------------|-----------|----------------------|\n")

		for _, m := range sentiment.Markets {
			question := m.Question
			if len(question) > 50 {
				question = question[:47] + "..."
			}
			sb.WriteString(fmt.Sprintf("| %s | %.1f%% | %.1f%% | $%.0fK | $%.0fK | %s |\n",
				question,
				m.YesProbability,
				m.NoProbability,
				m.Volume24hr/1000,
				m.Liquidity/1000,
				m.EndDateBeijing))
		}
		sb.WriteString("\n")
	}

	return sb.String()
}
