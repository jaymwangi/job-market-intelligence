"""Technology category definitions - static reference data."""

from enum import StrEnum
from typing import Dict, List, Set, Optional


class TechnologyCategory(StrEnum):
    """Technology job categories."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    FULL_STACK = "full_stack"
    DATA_ENGINEERING = "data_engineering"
    DATA_SCIENCE = "data_science"
    ML_AI = "ml_ai"
    DEVOPS = "devops"
    CLOUD = "cloud"
    SECURITY = "security"
    NETWORK = "network"
    MOBILE = "mobile"
    BLOCKCHAIN = "blockchain"
    GAME_DEV = "game_dev"
    QA = "qa"
    EMBEDDED = "embedded"
    SRE = "sre"
    PLATFORM = "platform"
    GENERAL_SOFTWARE = "general_software"
    OTHER = "other"
    # ============================================================
    # ✅ ADD MISSING CATEGORIES FROM YAML (found via grep)
    # ============================================================
    SYSTEMS = "systems"
    SOLUTIONS = "solutions"
    SUPPORT = "support"
    MANAGEMENT = "management"


# ============================================================
# Display Names
# ============================================================

CATEGORY_DISPLAY_NAMES: Dict[TechnologyCategory, str] = {
    TechnologyCategory.BACKEND: "Backend Development",
    TechnologyCategory.FRONTEND: "Frontend Development",
    TechnologyCategory.FULL_STACK: "Full Stack Development",
    TechnologyCategory.DATA_ENGINEERING: "Data Engineering",
    TechnologyCategory.DATA_SCIENCE: "Data Science",
    TechnologyCategory.ML_AI: "Machine Learning & AI",
    TechnologyCategory.DEVOPS: "DevOps",
    TechnologyCategory.CLOUD: "Cloud Engineering",
    TechnologyCategory.SECURITY: "Cybersecurity",
    TechnologyCategory.NETWORK: "Network Engineering",
    TechnologyCategory.MOBILE: "Mobile Development",
    TechnologyCategory.BLOCKCHAIN: "Blockchain & Web3",
    TechnologyCategory.GAME_DEV: "Game Development",
    TechnologyCategory.QA: "Quality Assurance",
    TechnologyCategory.EMBEDDED: "Embedded Systems",
    TechnologyCategory.SRE: "Site Reliability Engineering",
    TechnologyCategory.PLATFORM: "Platform Engineering",
    TechnologyCategory.GENERAL_SOFTWARE: "General Software Engineering",
    TechnologyCategory.OTHER: "Other Technology",
    # ============================================================
    # ✅ ADD DISPLAY NAMES FOR MISSING CATEGORIES
    # ============================================================
    TechnologyCategory.SYSTEMS: "Systems Engineering",
    TechnologyCategory.SOLUTIONS: "Solutions Engineering",
    TechnologyCategory.SUPPORT: "Technical Support",
    TechnologyCategory.MANAGEMENT: "Engineering Management",
}


# ============================================================
# Category Weights (for scoring)
# ============================================================

CATEGORY_WEIGHTS: Dict[TechnologyCategory, float] = {
    TechnologyCategory.BACKEND: 1.0,
    TechnologyCategory.FRONTEND: 1.0,
    TechnologyCategory.FULL_STACK: 1.2,
    TechnologyCategory.DATA_ENGINEERING: 1.1,
    TechnologyCategory.DATA_SCIENCE: 1.2,
    TechnologyCategory.ML_AI: 1.2,
    TechnologyCategory.DEVOPS: 1.1,
    TechnologyCategory.CLOUD: 1.0,
    TechnologyCategory.SECURITY: 1.1,
    TechnologyCategory.NETWORK: 1.1,
    TechnologyCategory.MOBILE: 1.0,
    TechnologyCategory.BLOCKCHAIN: 1.0,
    TechnologyCategory.GAME_DEV: 1.0,
    TechnologyCategory.QA: 0.9,
    TechnologyCategory.EMBEDDED: 1.0,
    TechnologyCategory.SRE: 1.1,
    TechnologyCategory.PLATFORM: 1.0,
    TechnologyCategory.GENERAL_SOFTWARE: 0.8,
    TechnologyCategory.OTHER: 0.5,
    # ============================================================
    # ✅ ADD WEIGHTS FOR MISSING CATEGORIES
    # ============================================================
    TechnologyCategory.SYSTEMS: 1.0,
    TechnologyCategory.SOLUTIONS: 1.0,
    TechnologyCategory.SUPPORT: 0.8,
    TechnologyCategory.MANAGEMENT: 0.9,
}


# ============================================================
# Category Keywords
# ============================================================

CATEGORY_KEYWORDS: Dict[TechnologyCategory, List[str]] = {
    TechnologyCategory.BACKEND: [
        # Languages
        "python", "java", "go", "golang", "rust", "c++", "c#", "ruby", "php",
        "scala", "kotlin", "elixir", "clojure", "erlang",
        # Frameworks
        "django", "flask", "fastapi", "spring", "spring boot", "rails", "laravel",
        "node.js", "nodejs", "express", "asp.net", ".net core", "gin", "echo",
        # Concepts
        "backend", "api", "microservices", "serverless", "rest api", "graphql",
        "grpc", "web services", "service layer", "business logic",
        # Tools
        "nginx", "apache", "gunicorn", "celery", "rabbitmq", "kafka",
        "postgresql", "mysql", "mongodb", "redis",
    ],
    TechnologyCategory.FRONTEND: [
        # Libraries/Frameworks
        "react", "angular", "vue", "vue.js", "svelte", "next.js", "nextjs",
        "gatsby", "remix", "solidjs", "qwik",
        # Languages
        "javascript", "typescript", "html", "css", "sass", "scss", "less",
        # Styling
        "tailwind", "bootstrap", "material ui", "chakra ui", "styled components",
        # Tools
        "webpack", "vite", "babel", "eslint", "prettier",
        # Concepts
        "frontend", "front-end", "ui", "user interface", "user experience",
        "responsive", "accessible", "design", "storybook",
        "client-side", "spa", "single page application", "pwa",
        "progressive web app", "web components",
    ],
    TechnologyCategory.FULL_STACK: [
        "full stack", "fullstack", "full-stack",
        "full stack developer", "fullstack engineer",
        "mean", "mern", "lamp", "jamstack",
    ],
    TechnologyCategory.DATA_ENGINEERING: [
        # Technologies
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "kafka", "spark", "hadoop", "flink", "beam", "druid", "clickhouse",
        "airflow", "dagster", "prefect", "dbt", "dataform",
        # Platforms
        "databricks", "snowflake", "bigquery", "redshift", "synapse",
        # Concepts
        "data", "etl", "elt", "pipeline", "warehouse", "data lake",
        "data lakehouse", "data mesh", "data fabric", "big data",
        "data engineering", "data infrastructure", "data platform",
        "streaming", "batch processing", "real-time",
    ],
    TechnologyCategory.DATA_SCIENCE: [
        # Languages
        "python", "r", "julia",
        # Libraries
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "scikit-learn", "statsmodels", "tensorflow", "pytorch",
        # Concepts
        "data science", "statistics", "probability", "linear algebra",
        "data analysis", "exploratory analysis", "eda",
        "feature engineering", "model evaluation", "validation",
        "a/b testing", "experimentation", "causal inference",
        "time series", "forecasting", "optimization",
    ],
    TechnologyCategory.ML_AI: [
        # Concepts
        "machine learning", "ml", "artificial intelligence", "ai",
        "deep learning", "neural networks", "transformer model", "transformers",
        "nlp", "natural language processing", "computer vision",
        "llm", "large language model", "generative ai", "genai",
        "retrieval augmented generation", "rag", "langchain",
        "reinforcement learning", "rl", "supervised learning",
        "unsupervised learning", "semi-supervised learning",
        "autoencoder", "gan", "diffusion model",
        # Roles
        "ml engineer", "ai engineer", "machine learning engineer",
        "prompt engineer", "mlops engineer",
        # Tools
        "tensorflow", "pytorch", "keras", "jax", "fastai",
        "hugging face", "transformers library", "llama", "openai",
        "anthropic", "cohere", "pinecone", "weaviate",
        "mlflow", "kubeflow", "sagemaker",
    ],
    TechnologyCategory.DEVOPS: [
        # Tools
        "docker", "kubernetes", "k8s", "terraform", "pulumi",
        "ansible", "chef", "puppet", "salt", "vagrant",
        "jenkins", "gitlab ci", "github actions", "circleci",
        "azure devops", "bamboo", "teamcity", "argo",
        # Platforms
        "aws", "azure", "gcp", "oracle cloud", "ibm cloud",
        # Concepts
        "devops", "infrastructure as code", "iac", "ci/cd",
        "configuration management", "automation", "orchestration",
        "containerization", "container", "orchestration",
        "immutable infrastructure", "declarative", "gitops",
        "observability", "monitoring", "alerting",
        # Tools (monitoring)
        "prometheus", "grafana", "datadog", "new relic", "splunk",
        "dynatrace", "appdynamics", "elastisearch", "logstash", "kibana",
        "elk stack", "elastic stack",
    ],
    TechnologyCategory.CLOUD: [
        # Providers
        "aws", "azure", "gcp", "google cloud", "amazon web services",
        "oracle cloud", "ibm cloud", "digital ocean", "cloudflare",
        "heroku", "netlify", "vercel", "railway",
        # Services
        "ec2", "s3", "rds", "lambda", "cloudfront", "vpc", "iam",
        "azure vm", "azure storage", "azure functions", "azure sql",
        "gce", "gke", "cloud storage", "bigtable", "cloud run",
        # Concepts
        "cloud migration", "cloud architecture", "cloud native",
        "multi-cloud", "hybrid cloud", "private cloud",
        "serverless", "faas", "function as a service",
        "cloud engineer", "cloud architect",
    ],
    TechnologyCategory.SECURITY: [
        # Concepts
        "security", "cybersecurity", "application security", "appsec",
        "information security", "infosec", "network security",
        "cloud security", "container security", "zero trust",
        "defense in depth", "security architecture",
        # Activities
        "penetration testing", "ethical hacking", "vulnerability assessment",
        "security scanning", "threat modeling", "incident response",
        "security operations", "soc", "security monitoring",
        "compliance", "audit", "risk management",
        # Frameworks/Standards
        "iso", "nist", "cmmc", "sox", "hipaa", "gdpr", "pci dss",
        "soc 2", "fedramp", "fisma",
        # Roles
        "security engineer", "security analyst", "security architect",
        "ciso", "security manager", "security consultant",
        # Tools
        "firewall", "ids", "ips", "waf", "sase", "swg", "casb",
        "splunk", "qradar", "crowdstrike", "palo alto", "fortinet",
    ],
    TechnologyCategory.NETWORK: [
        # Core networking
        "network",
        "networking",
        "network engineer",
        "network administrator",
        "network architect",
        "network infrastructure",
        # Hardware
        "cisco",
        "router",
        "routers",
        "switch",
        "switches",
        "catalyst",
        "nexus",
        "asa",
        # Routing / switching
        "routing",
        "switching",
        "bgp",
        "ospf",
        "eigrp",
        "vlan",
        "subnetting",
        "subnet",
        "nat",
        # Protocols / services
        "tcp/ip",
        "tcp",
        "udp",
        "ipv4",
        "ipv6",
        "dns",
        "dhcp",
        "snmp",
        # Network infrastructure
        "load balancer",
        "proxy",
        "reverse proxy",
        "vpn",
        "ipsec",
        # Network monitoring / analysis
        "wireshark",
        "netflow",
        "ipfix",
    ],
    TechnologyCategory.MOBILE: [
        # Platforms
        "ios", "android", "react native", "flutter", "swift",
        "kotlin", "objective-c", "java",
        # Frameworks
        "ionic", "xamarin", ".net maui", "native script",
        "capacitor", "cordova", "phonegap",
        # Concepts
        "mobile", "mobile app", "mobile application",
        "cross-platform", "multi-platform", "hybrid app",
        "native app", "app store", "google play",
        "mobile developer", "app developer",
        # Tools
        "xcode", "android studio", "fastlane", "appium",
        "swiftui", "jetpack compose", "react native",
    ],
    TechnologyCategory.BLOCKCHAIN: [
        # Concepts
        "blockchain", "web3", "cryptocurrency", "crypto",
        "smart contract", "dapp", "decentralized",
        "defi", "decentralized finance", "nft",
        "tokenization", "digital asset", "distributed ledger",
        # Platforms
        "ethereum", "solana", "polygon", "avalanche",
        "binance smart chain", "near", "polkadot", "cosmos",
        # Languages/Frameworks
        "solidity", "rust", "move", "vyper",
        "web3.js", "ethers.js", "hardhat", "truffle",
        "foundry", "openzeppelin",
        # Roles
        "blockchain developer", "web3 developer", "smart contract engineer",
    ],
    TechnologyCategory.GAME_DEV: [
        # Engines
        "unity", "unreal", "unreal engine", "godot",
        "cryengine", "lumberyard", "source engine",
        "game maker", "construct", "defold",
        # Concepts
        "game", "gaming", "game development", "game design",
        "gameplay", "game logic", "game mechanics",
        # Roles
        "game developer", "game designer", "game programmer",
        "technical artist", "game producer",
        # Skills
        "3d", "2d", "animation", "rendering", "shader",
        "physics", "collision detection", "ai in games",
        "opengl", "directx", "vulkan", "webgl",
        # Languages
        "c++", "c#", "lua", "python", "blueprints",
    ],
    TechnologyCategory.QA: [
        # Concepts
        "qa", "quality assurance", "testing", "test automation",
        "quality engineering", "quality analyst",
        # Types
        "manual testing", "automation testing",
        "unit testing", "integration testing", "e2e testing",
        "performance testing", "load testing", "stress testing",
        "regression testing", "smoke testing", "sanity testing",
        "usability testing", "accessibility testing",
        "security testing", "api testing", "ui testing",
        # Tools
        "selenium", "cypress", "playwright", "puppeteer",
        "jest", "pytest", "junit", "testng",
        "testrail", "qtest", "xray", "zephyr",
        "postman", "newman", "soapui",
        # Roles
        "qa engineer", "qa analyst", "qa lead",
        "test engineer", "automation engineer",
    ],
    TechnologyCategory.EMBEDDED: [
        # Concepts
        "embedded", "embedded systems", "firmware", "iot",
        "internet of things", "device driver", "hardware",
        "microcontroller", "microprocessor", "rtos",
        "real-time", "control systems", "automation",
        "industrial", "automotive", "medical devices",
        "consumer electronics", "robotics",
        # Languages
        "c", "c++", "assembly", "rust", "ada",
        "verilog", "vhdl", "system verilog",
        # Platforms
        "arm", "risc-v", "x86", "avr", "pic",
        "esp32", "esp8266", "arduino", "raspberry pi",
        "stm32", "nrf", "nxp",
        # Roles
        "embedded engineer", "firmware engineer",
        "iot engineer", "hardware engineer",
    ],
    TechnologyCategory.SRE: [
        # Concepts
        "sre", "site reliability engineering",
        "reliability", "availability", "performance",
        "scalability", "latency", "slo", "sli",
        "error budget", "incident management", "on-call",
        "capacity planning", "chaos engineering",
        # Tools
        "prometheus", "grafana", "thanos", "cortex",
        "victoriametrics", "influxdb", "telegraf",
        "alertmanager", "pagerduty", "opsgenie",
        "statuspage", "kibana", "logstash",
        # Roles
        "sre engineer", "site reliability engineer",
        "reliability engineer", "service engineer",
    ],
    TechnologyCategory.PLATFORM: [
        # Concepts
        "platform", "platform engineering",
        "developer platform", "internal platform",
        "internal developer platform", "idp",
        "developer experience", "dx", "developer productivity",
        "service mesh", "api gateway", "edge",
        "backstage", "humanitec", "crossplane",
        "port", "cortex", "opslevel",
        # Tools
        "kubernetes", "helm", "argocd", "flux",
        "istio", "linkerd", "consul", "envoy",
        "traefik", "nginx", "ha proxy",
        # Roles
        "platform engineer", "platform architect",
        "platform manager", "devops engineer",
    ],
    TechnologyCategory.GENERAL_SOFTWARE: [
        # General terms that indicate software development
        "software engineer", "software developer",
        "programmer", "coder", "software architect",
        "technical lead", "engineering manager", "tech lead",
        "software development", "software engineering",
        "agile", "scrum", "jira", "confluence",
        "git", "github", "bitbucket", "gitlab",
        "code review", "pr", "merge request",
    ],
    TechnologyCategory.OTHER: [
        # Catch-all for technology roles that don't fit categories
        # This category has low weight and is used as fallback
        "tech", "technical", "technology",
        "it", "information technology",
        "system", "systems", "infrastructure",
        "computer", "software", "solution",
    ],
    # ============================================================
    # ✅ ADD KEYWORDS FOR MISSING CATEGORIES
    # ============================================================
    TechnologyCategory.SYSTEMS: [
        "system", "systems", "system administration",
        "sysadmin", "windows server", "linux administration",
        "active directory", "infrastructure", "plm",
        "ptc", "windchill", "citrix",
    ],
    TechnologyCategory.SOLUTIONS: [
        "solutions", "solution", "solution architecture",
        "enterprise", "systems integration", "solution design",
    ],
    TechnologyCategory.SUPPORT: [
        "support", "helpdesk", "help desk",
        "technical support", "it support",
        "troubleshooting", "service desk",
    ],
    TechnologyCategory.MANAGEMENT: [
        "management", "manager", "engineering manager",
        "tech lead", "team lead", "technical lead",
        "director", "vp",
    ],
}


# ============================================================
# All Keywords Set (for quick lookup)
# ============================================================

ALL_CATEGORY_KEYWORDS: Set[str] = {
    keyword.lower()
    for keywords in CATEGORY_KEYWORDS.values()
    for keyword in keywords
}


# ============================================================
# Skill Display Names
# ============================================================

SKILL_DISPLAY_NAMES: Dict[str, str] = {
    # Languages
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "c++": "C++",
    "c#": "C#",
    "ruby": "Ruby",
    "php": "PHP",
    "scala": "Scala",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "objective-c": "Objective-C",
    "elixir": "Elixir",
    "clojure": "Clojure",
    "erlang": "Erlang",
    "r": "R",
    "julia": "Julia",
    "lua": "Lua",
    "ada": "Ada",
    "assembly": "Assembly",
    "verilog": "Verilog",
    "vhdl": "VHDL",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "sass": "Sass",
    "scss": "SCSS",
    "less": "Less",
    # Frameworks
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "rails": "Ruby on Rails",
    "laravel": "Laravel",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "asp.net": "ASP.NET",
    ".net core": ".NET Core",
    "gin": "Gin",
    "echo": "Echo",
    "react": "React",
    "angular": "Angular",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "svelte": "Svelte",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "gatsby": "Gatsby",
    "remix": "Remix",
    "solidjs": "SolidJS",
    "qwik": "Qwik",
    "tailwind": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "material ui": "Material UI",
    "chakra ui": "Chakra UI",
    "styled components": "Styled Components",
    "scikit-learn": "Scikit-Learn",
    "statsmodels": "StatsModels",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "keras": "Keras",
    "jax": "JAX",
    "fastai": "FastAI",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "plotly": "Plotly",
    "unity": "Unity",
    "unreal": "Unreal Engine",
    "godot": "Godot",
    "cryengine": "CryEngine",
    # Tools
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "pulumi": "Pulumi",
    "ansible": "Ansible",
    "chef": "Chef",
    "puppet": "Puppet",
    "salt": "Salt",
    "vagrant": "Vagrant",
    "jenkins": "Jenkins",
    "gitlab ci": "GitLab CI",
    "github actions": "GitHub Actions",
    "circleci": "CircleCI",
    "azure devops": "Azure DevOps",
    "bamboo": "Bamboo",
    "teamcity": "TeamCity",
    "argo": "Argo",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "thanos": "Thanos",
    "cortex": "Cortex",
    "victoriametrics": "VictoriaMetrics",
    "influxdb": "InfluxDB",
    "telegraf": "Telegraf",
    "alertmanager": "AlertManager",
    "pagerduty": "PagerDuty",
    "opsgenie": "Opsgenie",
    "statuspage": "StatusPage",
    "kibana": "Kibana",
    "logstash": "Logstash",
    "elk stack": "ELK Stack",
    "elastic stack": "Elastic Stack",
    "datadog": "Datadog",
    "new relic": "New Relic",
    "splunk": "Splunk",
    "dynatrace": "Dynatrace",
    "appdynamics": "AppDynamics",
    "webpack": "Webpack",
    "vite": "Vite",
    "babel": "Babel",
    "eslint": "ESLint",
    "prettier": "Prettier",
    "postman": "Postman",
    "newman": "Newman",
    "soapui": "SoapUI",
    "selenium": "Selenium",
    "cypress": "Cypress",
    "playwright": "Playwright",
    "puppeteer": "Puppeteer",
    "jest": "Jest",
    "pytest": "PyTest",
    "junit": "JUnit",
    "testng": "TestNG",
    "testrail": "TestRail",
    "qtest": "QTest",
    "xray": "Xray",
    "zephyr": "Zephyr",
    "appium": "Appium",
    "fastlane": "Fastlane",
    "xcode": "Xcode",
    "android studio": "Android Studio",
    "swiftui": "SwiftUI",
    "jetpack compose": "Jetpack Compose",
    "react native": "React Native",
    "flutter": "Flutter",
    "ionic": "Ionic",
    "xamarin": "Xamarin",
    ".net maui": ".NET MAUI",
    "native script": "NativeScript",
    "capacitor": "Capacitor",
    "cordova": "Cordova",
    "phonegap": "PhoneGap",
    # Cloud
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "Google Cloud",
    "amazon web services": "AWS",
    "oracle cloud": "Oracle Cloud",
    "ibm cloud": "IBM Cloud",
    "digital ocean": "DigitalOcean",
    "cloudflare": "Cloudflare",
    "heroku": "Heroku",
    "netlify": "Netlify",
    "vercel": "Vercel",
    "railway": "Railway",
    "ec2": "EC2",
    "s3": "S3",
    "rds": "RDS",
    "lambda": "Lambda",
    "cloudfront": "CloudFront",
    "vpc": "VPC",
    "iam": "IAM",
    "gce": "GCE",
    "gke": "GKE",
    "cloud storage": "Cloud Storage",
    "bigtable": "Bigtable",
    "cloud run": "Cloud Run",
    # Databases
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "kafka": "Apache Kafka",
    "spark": "Apache Spark",
    "hadoop": "Hadoop",
    "flink": "Apache Flink",
    "beam": "Apache Beam",
    "druid": "Druid",
    "clickhouse": "ClickHouse",
    "airflow": "Apache Airflow",
    "dagster": "Dagster",
    "prefect": "Prefect",
    "dbt": "dbt",
    "dataform": "Dataform",
    "databricks": "Databricks",
    "snowflake": "Snowflake",
    "bigquery": "BigQuery",
    "redshift": "Redshift",
    "synapse": "Azure Synapse",
    # Blockchain
    "blockchain": "Blockchain",
    "web3": "Web3",
    "cryptocurrency": "Cryptocurrency",
    "crypto": "Crypto",
    "smart contract": "Smart Contract",
    "dapp": "DApp",
    "defi": "DeFi",
    "nft": "NFT",
    "ethereum": "Ethereum",
    "solana": "Solana",
    "polygon": "Polygon",
    "avalanche": "Avalanche",
    "binance smart chain": "BSC",
    "near": "NEAR",
    "polkadot": "Polkadot",
    "cosmos": "Cosmos",
    "solidity": "Solidity",
    "web3.js": "web3.js",
    "ethers.js": "ethers.js",
    "hardhat": "Hardhat",
    "truffle": "Truffle",
    "foundry": "Foundry",
    "openzeppelin": "OpenZeppelin",
    # Security
    "security": "Security",
    "cybersecurity": "Cybersecurity",
    "appsec": "AppSec",
    "infosec": "InfoSec",
    "network security": "Network Security",
    "cloud security": "Cloud Security",
    "container security": "Container Security",
    "zero trust": "Zero Trust",
    "penetration testing": "Penetration Testing",
    "ethical hacking": "Ethical Hacking",
    "vulnerability assessment": "Vulnerability Assessment",
    "threat modeling": "Threat Modeling",
    "incident response": "Incident Response",
    "security operations": "SecOps",
    "soc": "SOC",
    "compliance": "Compliance",
    "audit": "Audit",
    "risk management": "Risk Management",
    "iso": "ISO",
    "nist": "NIST",
    "cmmc": "CMMC",
    "sox": "SOX",
    "hipaa": "HIPAA",
    "gdpr": "GDPR",
    "pci dss": "PCI DSS",
    "soc 2": "SOC 2",
    "fedramp": "FedRAMP",
    "fisma": "FISMA",
    "firewall": "Firewall",
    "ids": "IDS",
    "ips": "IPS",
    "waf": "WAF",
    "sase": "SASE",
    "swg": "SWG",
    "casb": "CASB",
    "crowdstrike": "CrowdStrike",
    "palo alto": "Palo Alto",
    "fortinet": "Fortinet",
    # Network
    "cisco": "Cisco",
    "router": "Router",
    "switch": "Switch",
    "bgp": "BGP",
    "ospf": "OSPF",
    "vlan": "VLAN",
    "tcp/ip": "TCP/IP",
    "dns": "DNS",
    "dhcp": "DHCP",
    "snmp": "SNMP",
    "vpn": "VPN",
    "ipsec": "IPSec",
    "wireshark": "Wireshark",
    "netflow": "NetFlow",
    # ✅ NEW: Systems/Solutions/Support/Management
    "plm": "PLM",
    "ptc": "PTC",
    "windchill": "Windchill",
    "citrix": "Citrix",
    "system administration": "System Administration",
    "systems administration": "Systems Administration",
    "sysadmin": "SysAdmin",
    "helpdesk": "Helpdesk",
    "help desk": "Help Desk",
    "technical support": "Technical Support",
    "it support": "IT Support",
    "engineering manager": "Engineering Manager",
    "tech lead": "Tech Lead",
    "team lead": "Team Lead",
}


# ============================================================
# Helper Functions
# ============================================================

def get_category_display_name(category: TechnologyCategory | str) -> str:
    """Get display name for a technology category."""
    if isinstance(category, str):
        try:
            category = TechnologyCategory(category)
        except ValueError:
            return category.title()
    return CATEGORY_DISPLAY_NAMES.get(category, category.value.title())


def get_category_weight(category: TechnologyCategory | str) -> float:
    """Get weight for a technology category."""
    if isinstance(category, str):
        try:
            category = TechnologyCategory(category)
        except ValueError:
            return 1.0
    return CATEGORY_WEIGHTS.get(category, 1.0)


def get_category_keywords(category: TechnologyCategory | str) -> List[str]:
    """Get keywords for a technology category."""
    if isinstance(category, str):
        try:
            category = TechnologyCategory(category)
        except ValueError:
            return []
    return CATEGORY_KEYWORDS.get(category, [])


def is_tech_keyword(keyword: str) -> bool:
    """Check if a keyword is in any technology category."""
    return keyword.lower() in ALL_CATEGORY_KEYWORDS


def find_category_for_keyword(keyword: str) -> TechnologyCategory | None:
    """Find which category a keyword belongs to."""
    keyword_lower = keyword.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if keyword_lower in keywords:
            return category
    return None


def get_skill_display_name(skill: str) -> str:
    """
    Get the display name for a skill.
    
    Example:
        "python" → "Python"
        "aws" → "AWS"
        "sql" → "SQL"
    """
    normalized = skill.strip().lower()
    return SKILL_DISPLAY_NAMES.get(normalized, skill.strip().title())


def normalize_skills_list(skills: List[str]) -> List[str]:
    """
    Normalize a list of skills to their display names.
    
    - Strips whitespace
    - Converts to lowercase for lookup
    - Returns display names (preserves casing)
    - Removes duplicates and sorts
    """
    if not skills:
        return []
    
    normalized = []
    seen = set()
    
    for skill in skills:
        if not skill or not skill.strip():
            continue
        
        display = get_skill_display_name(skill)
        key = display.lower()
        
        if key not in seen:
            seen.add(key)
            normalized.append(display)
    
    return sorted(normalized)


# ============================================================
# Export All
# ============================================================

__all__ = [
    "TechnologyCategory",
    "CATEGORY_DISPLAY_NAMES",
    "CATEGORY_WEIGHTS",
    "CATEGORY_KEYWORDS",
    "ALL_CATEGORY_KEYWORDS",
    "SKILL_DISPLAY_NAMES",
    "get_category_display_name",
    "get_category_weight",
    "get_category_keywords",
    "is_tech_keyword",
    "find_category_for_keyword",
    "get_skill_display_name",
    "normalize_skills_list",
]