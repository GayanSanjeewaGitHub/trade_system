"""
Configuration settings for the Trading Chatbot application.
Manages all environment variables and application constants.
"""

from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application Settings
    app_name: str = "TradingChatbot"
    app_version: str = "1.0.0"
    environment: str = "production"
    log_level: str = "INFO"
    debug: bool = False

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["*"]
    max_request_size: int = 10485760  # 10MB

    # LLM Configuration
    openai_api_key: str = "your-openai-api-key"
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout: int = 60

    # Pinecone Configuration
    pinecone_api_key: str = "your-pinecone-api-key"
    pinecone_environment: str = "gcp-starter"
    pinecone_index_name: str = "trading-chatbot-index"
    pinecone_dimension: int = 1536
    pinecone_metric: str = "cosine"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # Langfuse Configuration
    langfuse_public_key: str = "your-langfuse-public-key"
    langfuse_secret_key: str = "your-langfuse-secret-key"
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_enabled: bool = True

    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 8
    similarity_threshold: float = 0.5  # Lowered to allow more results
    embedding_model: str = "text-embedding-3-small"

    # Guardrails Configuration
    max_trade_amount: float = 100000.0
    min_trade_amount: float = 1.0
    max_message_length: int = 5000
    restricted_topics: List[str] = ["illegal", "violence", "hate", "manipulation" , "self-harm" ,"drugs" ,"gambling" ,"adult content"]
    profanity_threshold: float = 0.8

    # Agent Configuration
    max_agent_iterations: int = 10
    agent_timeout: int = 120
    max_tool_retries: int = 3
    
    # Intent Classification Keywords
    advisor_keywords: str = "buy,sell,trade,stock,price,invest,portfolio,shares,market,dividend,broker,execute,order,place order,market order,limit order,stop loss,take profit"
    faq_keywords: str = ("account,cds,fee,charge,policy,regulation,sec,cse,hours,contact,support,ipo,listing,open account,how to,what is,transfer,withdraw,deposit,statement,policies,"
                         "refund,balance,security,login,password,rewards,cashback,loyalty,trading policies,trading hours,customer support,account opening,fund transfer,"
                         "investment options,tax documents,platform features,mobile app,security measures,partnerships,api access,data privacy,compliance,risk management,"
                         "market analysis,educational resources,open a trading account,how to trade stocks,what are dividends,how to analyze market trends,investment strategies,"
                         "colombo stock exchange,stock broker,stockbroker,brokerage,cds account,central depository,settlement,t+2,t+3,clearing,dematerialized,demat,"
                         "aspi,all share price index,s&p sl20,market index,blue chip,listed companies,corporate disclosure,financial reports,quarterly reports,annual reports,"
                         "dividend announcement,rights issue,share buyback,director dealings,material events,compliance notice,regulatory notice,prospectus,initial public offering,"
                         "primary market,secondary market,ipo application,share allotment,oversubscription,certified investment advisor,investment advisor,bought note,sold note,"
                         "brokerage commission,sec levy,cds fee,stamp duty,transaction charges,trading fees,pattern day trader,good faith violation,margin trading,margin call,"
                         "forced liquidation,maintenance requirement,market hours,extended hours,pre-opening,post-closing,trading session,market capitalization,liquidity,"
                         "share price,current price,stock quote,ticker,volume,turnover,market depth,bid,ask,spread,last traded price,closing price,opening price,high,low,"
                         "52 week high,52 week low,price earnings ratio,pe ratio,earnings per share,eps,book value,market value,face value,par value,dividend yield,payout ratio,"
                         "ex-dividend date,record date,payment date,declaration date,interim dividend,final dividend,special dividend,bonus shares,stock split,reverse split,"
                         "shareholder,equity holder,institutional investor,retail investor,foreign investor,local investor,strategic investor,promoter,public float,free float,"
                         "block deal,bulk deal,insider trading,market manipulation,price rigging,front running,circular trading,wash sale,pump and dump,scalping,day trading,"
                         "swing trading,position trading,long term investing,short selling,naked short,covered short,arbitrage,hedging,speculation,fundamental analysis,"
                         "technical analysis,chart patterns,trend analysis,support,resistance,breakout,breakdown,consolidation,volatility,beta,correlation,diversification,"
                         "asset allocation,rebalancing,risk tolerance,risk appetite,investment horizon,time horizon,goal based investing,retirement planning,wealth creation,"
                         "capital gains,capital appreciation,unrealized gains,realized gains,capital loss,tax on dividends,withholding tax,capital gains tax,investment income,"
                         "portfolio management,portfolio tracking,portfolio review,portfolio performance,benchmark,outperform,underperform,alpha,beta,sharpe ratio,sortino ratio,"
                         "maximum drawdown,recovery period,compound annual growth rate,cagr,absolute returns,annualized returns,time weighted returns,money weighted returns,"
                         "account statement,transaction history,holding statement,contract note,tax statement,annual statement,quarterly statement,monthly statement,e-statement,"
                         "paper statement,account balance,available balance,cash balance,margin balance,buying power,withdrawal,deposit,fund transfer,bank transfer,wire transfer,"
                         "payment gateway,payment methods,settlement account,linked bank account,bank details update,nominee,nomination,beneficiary,joint account,corporate account,"
                         "trust account,custodian account,nri account,foreign account,institutional account,individual account,minor account,guardian,power of attorney,mandate,"
                         "kyc,know your customer,aml,anti money laundering,cft,combating financing of terrorism,due diligence,enhanced due diligence,risk based approach,customer identification,"
                         "identity verification,address proof,income proof,bank statement,utility bill,passport,national id,driving license,pan card,tax id,ssn,ein,tin,"
                         "two factor authentication,2fa,otp,one time password,biometric,fingerprint,face recognition,security token,session timeout,password policy,password reset,"
                         "forgot password,account locked,account suspended,account closure,dormant account,inactive account,reactivation,account recovery,dispute resolution,"
                         "arbitration,ombudsman,grievance,complaint,customer care,helpdesk,support ticket,escalation,feedback,suggestion,testimonial,review,rating,"
                         "user guide,tutorial,faq,frequently asked questions,help center,knowledge base,video tutorial,webinar,workshop,training,certification,accreditation,"
                         "investor education,financial literacy,market basics,trading basics,investment basics,beginner guide,getting started,first steps,onboarding,"
                         "mobile trading,web trading,desktop application,trading platform,order types,market order,limit order,stop order,stop limit,trailing stop,good till cancelled,"
                         "gtc,day order,immediate or cancel,ioc,fill or kill,fok,all or none,aon,iceberg order,hidden order,disclosed quantity,minimum quantity,trigger price,"
                         "order modification,order cancellation,order status,order confirmation,order execution,partial fill,complete fill,order rejection,order expiry,"
                         "trading rules,trading regulations,listing requirements,delisting,suspension,circuit breaker,price band,tick size,lot size,board lot,odd lot,"
                         "market maker,liquidity provider,designated market maker,dmm,specialist,floor trader,algorithmic trading,high frequency trading,hft,dark pool,"
                         "stock exchange,bourse,equity market,capital market,securities market,financial market,emerging market,frontier market,developed market,stock market crash,"
                         "market correction,bear market,bull market,sideways market,range bound,trending market,momentum,reversal,continuation,gap up,gap down,opening gap,"
                         "world federation of exchanges,wfe,safe,south asian federation,sustainable stock exchanges,sse initiative,international affiliation,global standards,"
                         "iso certification,business continuity,disaster recovery,information security,cybersecurity,data protection,privacy policy,gdpr,data breach,encryption,"
                         "ssl,tls,secure connection,https,firewall,intrusion detection,penetration testing,vulnerability assessment,security audit,compliance audit,"
                         "regulatory compliance,statutory compliance,listing compliance,disclosure norms,insider trading regulations,takeover code,substantial acquisition,creeping acquisition,"
                         "open offer,delisting offer,buyback offer,exit offer,competitive bid,negotiated deal,scheme of arrangement,merger,acquisition,amalgamation,demerger,spin off,"
                         "corporate action,bonus issue,rights issue,preferential allotment,private placement,public issue,follow on public offer,fpo,qualified institutional placement,qip,"
                         "american depositary receipt,adr,global depositary receipt,gdr,foreign currency convertible bond,fccb,external commercial borrowing,ecb,foreign direct investment,fdi,"
                         "foreign portfolio investment,fpi,foreign institutional investor,fii,qualified foreign investor,qfi,participatory note,p-note,offshore derivative instrument,odi,"
                         "depository receipt,conversion ratio,conversion price,redemption,callable,puttable,convertible,non convertible,secured,unsecured,senior,subordinated,"
                         "investment grade,speculative grade,credit rating,rating agency,rating upgrade,rating downgrade,rating outlook,rating watch,default,bankruptcy,liquidation,"
                         "insolvency,restructuring,debt restructuring,equity restructuring,one time settlement,ots,strategic debt restructuring,sdr,asset reconstruction,bad bank,"
                         "non performing asset,npa,stressed asset,impaired asset,provisioning,write off,recovery,resolution,haircut,cramdown,super priority,waterfall mechanism,"
                         "what is cse,what is colombo stock exchange,what is cds,what is central depository,what is aspi,what is s&p sl20,what is ipo,what is primary market,"
                         "what is secondary market,what is stock broker,what is brokerage,what is trading,what is investing,what is dividend,what is capital gains,what is portfolio,"
                         "what is market order,what is limit order,what is stop loss,what is settlement,what is t+2,what is t+3,what is margin,what is leverage,what is short selling,"
                         "how to open cds account,how to create account,how to open trading account,how to select broker,how to choose stockbroker,how to buy shares,how to sell shares,"
                         "how to place order,how to check prices,how to monitor portfolio,how to withdraw funds,how to deposit money,how to transfer shares,how to apply ipo,"
                         "how to read prospectus,how to analyze stocks,how to calculate returns,how to pay taxes,how to get statement,how to update details,how to close account,"
                         "how to file complaint,how to contact support,how long settlement,how much fees,how much commission,how much minimum investment,how much charges,"
                         "how do i open,how do i create,how do i register,how do i start,how can i open,open account online,create account online,register online,apply online,"
                         "mobile app registration,app account opening,download cse app,cse mobile application,asia securities,stockbroker selection,choose broker,select stockbroker,"
                         "upload documents,nic upload,proof of residency,bank book upload,selfie verification,identity verification,document requirements,required documents,"
                         "peps questionnaire,politically exposed person,verification process,account verification,application process,online application,application form,submit application,"
                         "account approval,verification time,24 hours approval,instant approval,quick approval,fast account opening,easy registration,simple signup,"
                         "personal information,residential details,bank account details,employment details,terms and conditions,agree to terms,submit form,complete registration,"
                         "when trading hours,when market open,when market close,when dividend payment,when ipo,when can i sell,when will i receive shares,when statement generated,"
                         "where is cse located,where to open account,where to check prices,where to get help,where to download app,where to find information,where regional offices,"
                         "why invest,why stock market,why need cds account,why need broker,why prices change,why suspended,why delisted,why dividend not received,why order rejected,"
                         "can i trade without broker,can i have multiple accounts,can i transfer to another broker,can i sell on same day,can i cancel order,can foreigners invest,"
                         "is it safe,is account free,is trading risky,is margin allowed,is short selling allowed,is mobile app available,is my money protected,is cse regulated,"
                         "who regulates cse,who can open account,who are market makers,who can be nominee,who is sec,who are board members,who are certified advisors,"
                         "tell me about,explain,describe,information about,details about,learn about,understand,clarify,difference between,compare,versus,vs")

    # MCP Configuration
    mcp_server_url: str = "http://localhost:8001"
    mcp_timeout: int = 30
    mcp_enabled: bool = True

    # Rate Limiting
    rate_limit_per_minute: int = 60000
    rate_limit_per_hour: int = 100000

    # Session Management
    session_timeout: int = 36000  # 1 hour
    max_conversation_history: int = 500

    # Monitoring & Evaluation
    enable_auto_eval: bool = True
    eval_sample_rate: float = 0.1
    metrics_retention_days: int = 30

    # Redis Configuration (optional for caching)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    cache_ttl: int = 3600

    # Document Processing
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: List[str] = [".pdf", ".txt", ".md", ".docx"]
    temp_upload_dir: str = "/tmp/uploads"

    # Logging
    log_format: str = "json"
    log_file: Optional[str] = None
    log_rotation: str = "1 day"
    log_retention: str = "30 days"

    def get_openai_config(self) -> dict:
        """Get OpenAI configuration dictionary."""
        return {
            "api_key": self.openai_api_key,
            "model": self.llm_model,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
            "timeout": self.llm_timeout,
        }

    def get_pinecone_config(self) -> dict:
        """Get Pinecone configuration dictionary."""
        return {
            "api_key": self.pinecone_api_key,
            "environment": self.pinecone_environment,
            "index_name": self.pinecone_index_name,
            "dimension": self.pinecone_dimension,
            "metric": self.pinecone_metric,
        }

    def get_langfuse_config(self) -> dict:
        """Get Langfuse configuration dictionary."""
        return {
            "public_key": self.langfuse_public_key,
            "secret_key": self.langfuse_secret_key,
            "host": self.langfuse_host,
            "enabled": self.langfuse_enabled,
        }

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ["development", "dev"]


    def get_advisor_keywords_list(self) -> List[str]:
        """Get advisor keywords as a list."""
        return [k.strip().lower() for k in self.advisor_keywords.split(",") if k.strip()]
    
    def get_faq_keywords_list(self) -> List[str]:
        """Get FAQ keywords as a list."""
        return [k.strip().lower() for k in self.faq_keywords.split(",") if k.strip()]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to avoid reloading settings on every call.
    """
    return Settings()


# Global settings instance
settings = get_settings()