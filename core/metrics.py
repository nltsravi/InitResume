from prometheus_client import Counter

# Metrics definition for Prometheus monitoring

# 1. Tokens used per day/request
TOKENS_USED = Counter(
    "tokens_used_total", 
    "Total count of LLM tokens consumed", 
    ["model", "type"] # model: e.g. gpt-4-turbo, type: input or output
)

# 2. Application success rate tracker
APPLICATION_STATUS = Counter(
    "application_submissions_total", 
    "Total job applications submitted", 
    ["status"] # status: success or failure
)

# 3. Playwright automation crash rate tracker
PLAYWRIGHT_CRASHES = Counter(
    "playwright_crashes_total", 
    "Total Playwright execution crashes (DOM changes, selector timeouts, etc.)", 
    ["reason"]
)
