const knowledge = require('../knowledge.json');

const KNOWLEDGE_TEXT = knowledge.map(k => `Q: ${k.q}\nA: ${k.a}`).join('\n\n');

const SYSTEM_PROMPT = `You are Mila Arty's personal assistant on her portfolio website.

RULES:
1. Answer ONLY based on the information below
2. Do NOT invent facts, prices, or services
3. If you don't have the info — say "I don't have that information, but you can reach Mila directly via the contacts on this page."
4. Keep answers concise and friendly
5. Answer in the same language the user writes in

About Mila:
${KNOWLEDGE_TEXT}`;

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const API_KEY = process.env.MINIMAX_API_KEY;
  if (!API_KEY) {
    console.error('[CHAT] MINIMAX_API_KEY is not set');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  const { message } = req.body || {};
  if (!message) {
    console.warn('[CHAT] Empty message received');
    return res.status(400).json({ error: 'No message provided' });
  }

  const timestamp = new Date().toISOString();
  console.log(`[CHAT ${timestamp}] User: "${message}"`);

  try {
    const apiResponse = await fetch('https://api.minimax.io/anthropic/v1/messages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'MiniMax-M2.5',
        messages: [{ role: 'user', content: message }],
        max_tokens: 2000,
        temperature: 0.7,
        system: SYSTEM_PROMPT
      })
    });

    const data = await apiResponse.json();

    if (!apiResponse.ok) {
      console.error(`[CHAT ${timestamp}] API error ${apiResponse.status}:`, JSON.stringify(data));
      return res.status(502).json({ error: 'AI service error', details: data.error?.message || 'Unknown' });
    }

    const reply = data?.content?.[0]?.text;
    if (!reply) {
      console.error(`[CHAT ${timestamp}] Unexpected response format:`, JSON.stringify(data));
      return res.status(502).json({ error: 'Unexpected AI response format' });
    }

    console.log(`[CHAT ${timestamp}] Bot: "${reply.substring(0, 120)}${reply.length > 120 ? '...' : ''}"`);
    console.log(`[CHAT ${timestamp}] Tokens — input: ${data.usage?.input_tokens || '?'}, output: ${data.usage?.output_tokens || '?'}`);

    return res.status(200).json({ response: reply });

  } catch (err) {
    console.error(`[CHAT ${timestamp}] Exception:`, err.message);
    return res.status(500).json({ error: 'Internal server error' });
  }
};
