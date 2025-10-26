# Intent Classification Configuration

## Overview
The intent classification system now uses configurable keywords stored in the `.env` file, allowing you to customize agent routing without modifying code.

## Configuration Files

### 1. Environment Variables (.env)
Copy `.env.example` to `.env` and customize these settings:

```bash
# ADVISOR_KEYWORDS: Keywords that trigger routing to the Advisor Agent
ADVISOR_KEYWORDS=buy,sell,trade,stock,price,invest,portfolio,shares,market,dividend,broker

# FAQ_KEYWORDS: Keywords that trigger routing to the FAQ Agent
FAQ_KEYWORDS=account,cds,fee,charge,policy,regulation,sec,cse,hours,contact,support,ipo,listing,open account,how to,what is,transfer,withdraw,deposit,statement
```

## How It Works

### Classification Logic

1. **When LLM is NOT available** (fallback mode):
   - The system checks user input against the configured keywords
   - **Priority Order:**
     1. First checks `ADVISOR_KEYWORDS` - if any match → routes to Advisor Agent
     2. Then checks `FAQ_KEYWORDS` - if any match → routes to FAQ Agent
     3. **Default behavior:** If no keywords match, still routes to FAQ Agent (as a safe fallback)

2. **When LLM is available**:
   - Uses AI-powered classification for more intelligent routing
   - Considers context and intent beyond simple keyword matching

### Default Keywords

#### ADVISOR_KEYWORDS
Triggers routing to the **Advisor Agent** for trading-related queries:
- `buy`, `sell`, `trade`, `stock`, `price`
- `invest`, `portfolio`, `shares`, `market`
- `dividend`, `broker`

**Example queries that match:**
- "I want to buy shares of Company X"
- "What's the current stock price?"
- "How do I invest in the market?"

#### FAQ_KEYWORDS
Triggers routing to the **FAQ Agent** for general information queries:
- `account`, `cds`, `fee`, `charge`, `policy`
- `regulation`, `sec`, `cse`, `hours`
- `contact`, `support`, `ipo`, `listing`
- `open account`, `how to`, `what is`
- `transfer`, `withdraw`, `deposit`, `statement`

**Example queries that match:**
- "How do I open a CDS account?"
- "What are the trading fees?"
- "What is the CSE?"
- "How to contact support?"

## Customization Guide

### Adding New Keywords

1. Open your `.env` file
2. Add keywords to the appropriate list (comma-separated):

```bash
# Add "equity" and "bond" to advisor keywords
ADVISOR_KEYWORDS=buy,sell,trade,stock,price,invest,portfolio,shares,market,dividend,broker,equity,bond

# Add "complain" and "issue" to FAQ keywords
FAQ_KEYWORDS=account,cds,fee,charge,policy,regulation,sec,cse,hours,contact,support,ipo,listing,open account,how to,what is,transfer,withdraw,deposit,statement,complain,issue
```

3. Restart the application to apply changes

### Best Practices

1. **Keyword Selection:**
   - Use lowercase keywords (the system converts input to lowercase automatically)
   - Include common variations and synonyms
   - Keep keywords specific to avoid false matches

2. **Testing:**
   - Test your keywords with sample queries
   - Monitor agent routing in logs
   - Adjust keywords based on user behavior

3. **Maintenance:**
   - Review keyword effectiveness periodically
   - Add new keywords based on common user queries
   - Remove keywords that cause misclassification

## FAQ Default Behavior

The FAQ agent serves as the **default fallback** for queries that don't match any keywords. This ensures:
- Users always get a response
- Unclear queries are handled gracefully
- General questions are properly addressed

## Code Implementation

### Settings (src/config/settings.py)
```python
# Intent Classification Keywords
advisor_keywords: str = "buy,sell,trade,stock,price,invest,portfolio,shares,market,dividend,broker"
faq_keywords: str = "account,cds,fee,charge,policy,regulation,sec,cse,hours,contact,support,ipo,listing,open account,how to,what is,transfer,withdraw,deposit,statement"

def get_advisor_keywords_list(self) -> List[str]:
    """Get advisor keywords as a list."""
    return [k.strip().lower() for k in self.advisor_keywords.split(",") if k.strip()]

def get_faq_keywords_list(self) -> List[str]:
    """Get FAQ keywords as a list."""
    return [k.strip().lower() for k in self.faq_keywords.split(",") if k.strip()]
```

### Controller (src/agents/controller.py)
```python
# Get keyword lists from settings
advisor_keywords = settings.get_advisor_keywords_list()
faq_keywords = settings.get_faq_keywords_list()

# Check for advisor keywords first
if any(keyword in user_input_lower for keyword in advisor_keywords):
    intent = "ADVISOR"
# Check for FAQ keywords, or default to FAQ
elif any(keyword in user_input_lower for keyword in faq_keywords) or True:
    intent = "FAQ"
```

## Monitoring & Debugging

### Check Classification in Logs
```
Intent classified using keywords, intent=ADVISOR
Intent classified using keywords, intent=FAQ
```

### Common Issues

**Issue:** Queries being misrouted
- **Solution:** Review and refine your keywords in `.env`

**Issue:** Too many queries going to one agent
- **Solution:** Balance keyword lists between agents

**Issue:** Keywords not taking effect
- **Solution:** Ensure you've restarted the application after .env changes

## Migration Notes

If you're upgrading from the previous hardcoded version:
1. Copy `.env.example` to `.env`
2. Customize `ADVISOR_KEYWORDS` and `FAQ_KEYWORDS` as needed
3. The default keywords match the previous hardcoded behavior
4. No code changes required - configuration is now externalized

## Support

For questions or issues with intent classification:
1. Check the logs for classification decisions
2. Review your keyword configuration in `.env`
3. Test with sample queries
4. Adjust keywords iteratively based on results
