package mcp

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

const (
	ProviderCLI          = "cli"
	DefaultCLICommand    = "gemini"
	DefaultCLIModel      = "gemini-2.5-flash"
	DefaultCLIOutputFormat = "text"
)

// CLIClient executes AI via local CLI command (e.g., gemini CLI)
type CLIClient struct {
	Command      string        // CLI command (e.g., "gemini", "claude", "ollama")
	Model        string        // Model name
	OutputFormat string        // Output format (text, json)
	ExtraArgs    []string      // Additional CLI arguments
	Timeout      time.Duration // Command timeout
	logger       Logger
}

// NewCLIClient creates a CLI-based AI client
func NewCLIClient(opts ...ClientOption) AIClient {
	cfg := DefaultConfig()
	for _, opt := range opts {
		opt(cfg)
	}

	client := &CLIClient{
		Command:      DefaultCLICommand,
		Model:        DefaultCLIModel,
		OutputFormat: DefaultCLIOutputFormat,
		ExtraArgs:    []string{},
		Timeout:      cfg.Timeout,
		logger:       cfg.Logger,
	}

	return client
}

// NewGeminiCLIClient creates a Gemini CLI client
func NewGeminiCLIClient(opts ...ClientOption) AIClient {
	client := NewCLIClient(opts...).(*CLIClient)
	client.Command = "gemini"
	client.Model = "gemini-2.5-flash"
	client.ExtraArgs = []string{"--output-format", "text", "--allowed-tools", ""}
	return client
}

// NewOllamaCLIClient creates an Ollama CLI client
func NewOllamaCLIClient(model string, opts ...ClientOption) AIClient {
	client := NewCLIClient(opts...).(*CLIClient)
	client.Command = "ollama"
	client.Model = model
	if client.Model == "" {
		client.Model = "llama3"
	}
	return client
}

func (c *CLIClient) SetAPIKey(apiKey string, customURL string, customModel string) {
	// CLI doesn't need API key, but can set model
	if customModel != "" {
		c.Model = customModel
		c.logger.Infof("🔧 [CLI] Using model: %s", c.Model)
	}
	if customURL != "" {
		// customURL can be used as command path
		c.Command = customURL
		c.logger.Infof("🔧 [CLI] Using command: %s", c.Command)
	}
}

func (c *CLIClient) SetTimeout(timeout time.Duration) {
	c.Timeout = timeout
}

func (c *CLIClient) CallWithMessages(systemPrompt, userPrompt string) (string, error) {
	return c.executeCommand(systemPrompt, userPrompt)
}

func (c *CLIClient) CallWithRequest(req *Request) (string, error) {
	// Extract system and user prompts from request
	var systemPrompt, userPrompt string
	for _, msg := range req.Messages {
		switch msg.Role {
		case "system":
			systemPrompt = msg.Content
		case "user":
			userPrompt = msg.Content
		}
	}
	return c.executeCommand(systemPrompt, userPrompt)
}

func (c *CLIClient) executeCommand(systemPrompt, userPrompt string) (string, error) {
	var args []string

	switch c.Command {
	case "gemini":
		args = c.buildGeminiArgs(systemPrompt)
	case "ollama":
		args = c.buildOllamaArgs(systemPrompt)
	case "claude":
		args = c.buildClaudeArgs(systemPrompt)
	default:
		args = c.buildGenericArgs(systemPrompt)
	}

	c.logger.Infof("🚀 [CLI] Executing: %s %v", c.Command, args)

	cmd := exec.Command(c.Command, args...)

	// Set proxy for CLI if configured via environment
	if httpProxy := os.Getenv("CLI_HTTP_PROXY"); httpProxy != "" {
		cmd.Env = append(cmd.Environ(),
			"http_proxy="+httpProxy,
			"https_proxy="+httpProxy,
		)
	}

	// Pass user prompt via stdin
	cmd.Stdin = strings.NewReader(userPrompt)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	// Set timeout
	if c.Timeout > 0 {
		done := make(chan error, 1)
		go func() {
			done <- cmd.Run()
		}()

		select {
		case err := <-done:
			if err != nil {
				return "", fmt.Errorf("CLI command failed: %w, stderr: %s", err, stderr.String())
			}
		case <-time.After(c.Timeout):
			cmd.Process.Kill()
			return "", fmt.Errorf("CLI command timeout after %v", c.Timeout)
		}
	} else {
		if err := cmd.Run(); err != nil {
			return "", fmt.Errorf("CLI command failed: %w, stderr: %s", err, stderr.String())
		}
	}

	result := strings.TrimSpace(stdout.String())
	c.logger.Infof("✓ [CLI] Response length: %d chars", len(result))

	return result, nil
}

// buildGeminiArgs builds arguments for Gemini CLI
// Usage: cat input.txt | gemini -m model --output-format text --allowed-tools '' "system prompt"
func (c *CLIClient) buildGeminiArgs(systemPrompt string) []string {
	args := []string{"-m", c.Model}
	args = append(args, c.ExtraArgs...)
	if systemPrompt != "" {
		args = append(args, systemPrompt)
	}
	return args
}

// buildOllamaArgs builds arguments for Ollama CLI
// Usage: echo "prompt" | ollama run model
func (c *CLIClient) buildOllamaArgs(systemPrompt string) []string {
	args := []string{"run", c.Model}
	if systemPrompt != "" {
		args = append(args, "--system", systemPrompt)
	}
	args = append(args, c.ExtraArgs...)
	return args
}

// buildClaudeArgs builds arguments for Claude CLI
func (c *CLIClient) buildClaudeArgs(systemPrompt string) []string {
	args := []string{}
	if c.Model != "" {
		args = append(args, "--model", c.Model)
	}
	if systemPrompt != "" {
		args = append(args, "--system", systemPrompt)
	}
	args = append(args, c.ExtraArgs...)
	return args
}

// buildGenericArgs builds generic CLI arguments
func (c *CLIClient) buildGenericArgs(systemPrompt string) []string {
	args := []string{}
	if c.Model != "" {
		args = append(args, "--model", c.Model)
	}
	args = append(args, c.ExtraArgs...)
	if systemPrompt != "" {
		args = append(args, systemPrompt)
	}
	return args
}

// SetCommand sets the CLI command
func (c *CLIClient) SetCommand(command string) {
	c.Command = command
}

// SetExtraArgs sets additional CLI arguments
func (c *CLIClient) SetExtraArgs(args []string) {
	c.ExtraArgs = args
}
