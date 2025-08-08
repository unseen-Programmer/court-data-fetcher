// server.js
const express = require('express');
const bodyParser = require('body-parser');
const { scrapeCourtData } = require('./services/courtScraper');

const app = express();
app.use(bodyParser.json());

// Basic input validation helper
function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

app.post('/fetch', async (req, res) => {
  const { url } = req.body;
  if (!url || typeof url !== 'string' || !isValidUrl(url)) {
    return res.status(400).json({ error: 'A valid URL must be provided.' });
  }
  const data = await scrapeCourtData(url);
  res.json(data);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
