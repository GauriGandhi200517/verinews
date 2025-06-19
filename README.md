# 📰 VeriNews - Fake News Detection System 🤖

VeriNews is an advanced news credibility analysis platform that empowers users to detect misleading or false information in news articles using cutting-edge machine learning and AI technologies. Stay informed and make smarter news choices! 🕵️‍♂️✨

---

## 🚀 Features

- 🌎 **Multi-Country News Coverage** — Access news from 50+ countries worldwide!
- 🗂️ **Category Filtering** — Focus on what matters: business, sports, tech, politics, and more.
- 🔍 **Search Functionality** — Quickly find news on any topic from trusted sources.
- 🧠 **Dual Analysis System**:
  - Local machine learning model for instant credibility checks
  - Optional Google Gemini AI integration for deep-dive analysis and recommendations
- 📊 **Visual Confidence Indicators** — Instantly see how trustworthy an article is.
- 📱 **Responsive Design** — Use VeriNews on desktop and mobile devices.
- 🔌 **RESTful API** — Seamlessly integrate news analysis into your own apps.

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- NewsAPI account (free tier available)
- Google Gemini API key (optional, for advanced analysis)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/GauriGandhi200517/verinews.git
   cd verinews
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API keys:**  
   Create a `.env` file in the project root:
   ```
   NEWS_API_KEY=your_news_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Run the app:**
   ```bash
   python app.py
   ```

5. **Open your browser:**
   ```
   http://localhost:5000
   ```

---

## 🖱️ Usage Guide

### Browsing News

- Select a country to view regional news
- Choose a category to filter by topic
- Use the search box for specific news topics

### Analyzing Articles

1. Browse news cards on the homepage
2. Click **Analyze** on any article
3. Optionally enable **Use Gemini AI** for deeper analysis
4. View:
   - Classification (Real, Fake, or Uncertain)
   - Confidence level
   - Gemini AI's insights and recommendations (if enabled)
   - Fact-checking tips

### API Usage

Integrate VeriNews into your own projects:

```python
import requests

url = "http://localhost:5000/api/analyze"
data = {
    "content": "Your article text here",
    "title": "Article title",
    "source": "Source name",
    "use_gemini": True
}

response = requests.post(url, json=data)
result = response.json()
print(result)
```

---

## 🛠️ Technology Stack

- **Backend:** Flask (Python)
- **Machine Learning:** TensorFlow, Hugging Face Transformers
- **AI Integration:** Google Gemini API
- **Frontend:** HTML, CSS, JavaScript, Materialize CSS
- **External APIs:** NewsAPI

---

## ⚠️ Limitations

- Provides guidance, not absolute truth — always verify critical details!
- Best results with English-language content
- Free NewsAPI tier: 100 requests/day, delayed headlines
- Gemini API requires an API key and has usage quotas

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Pull requests are welcome!  
To contribute:

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

Stay smart, stay informed — with VeriNews! 📰✨
