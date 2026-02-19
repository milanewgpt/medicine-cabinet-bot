/**
 * RAG Script - Загрузка данных с сайта для чатбота
 * 
 * Использование:
 *   node rag.js https://example.com          - загрузить с URL
 *   node rag.js --file mydata.json          - загрузить из файла
 *   node rag.js --text "текст информации"   - из командной строки
 * 
 * Создает knowledge.json для server.js
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// Аргументы
const args = process.argv.slice(2);
const urlArg = args.find(a => !a.startsWith('--'));
const fileArg = args.find(a => a.startsWith('--file'));
const textArg = args.find(a => a.startsWith('--text'));
const outputFile = path.join(__dirname, 'knowledge.json');

async function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    
    client.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

function extractText(html) {
  // Удаляем скрипты и стили
  let text = html
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  
  // Удаляем лишние пробелы
  text = text.replace(/ {2,}/g, ' ');
  
  return text;
}

function parseToQASections(text) {
  // Ищем секции с ценами и услугами
  const sections = [];
  
  // Паттерны для поиска
  const patterns = [
    /(?:услуг[аы]?|сервис|услуга)[^\.]+\.?\s*[\d\s]+(?:руб|₽|USD|\$)/gi,
    /(?:цена|стоимость|прайс)[^\.]+[\d\s]+(?:руб|₽|USD|\$)/gi,
    /•\s*[^\n]+/g,
    /-\s*[^\n]+/g
  ];
  
  patterns.forEach(pattern => {
    const matches = text.match(pattern);
    if (matches) {
      sections.push(...matches);
    }
  });
  
  return sections;
}

async function main() {
  let data = '';
  
  if (fileArg) {
    // Из файла
    const filePath = fileArg.replace('--file', '').trim();
    data = fs.readFileSync(filePath, 'utf-8');
    console.log('Загружено из файла');
  } 
  else if (textArg) {
    // Из командной строки
    data = textArg.replace('--text', '').trim().replace(/^["']|["']$/g, '');
    console.log('Использован текст из аргументов');
  } 
  else if (urlArg) {
    // С URL
    console.log(`Загрузка с ${urlArg}...`);
    const html = await fetchUrl(urlArg);
    data = extractText(html);
    console.log(`Извлечено ${data.length} символов`);
  } 
  else {
    console.log('Использование:');
    console.log('  node rag.js <url>              - загрузить с сайта');
    console.log('  node rag.js --file <file>     - из файла');
    console.log('  node rag.js --text "текст"    - из командной строки');
    process.exit(1);
  }
  
  // Парсим в Q&A формат
  let knowledge;
  
  try {
    // Пробуем JSON
    knowledge = JSON.parse(data);
  } catch {
    // Текст - разбиваем на секции
    const sections = parseToQASections(data);
    
    if (sections.length > 0) {
      // Создаем Q&A из найденных секций
      knowledge = sections.map((section, i) => ({
        q: `Информация ${i + 1}`,
        a: section.trim()
      }));
    } else {
      // Используем весь текст
      knowledge = [{ q: 'Базовая информация', a: data }];
    }
  }
  
  // Сохраняем
  fs.writeFileSync(outputFile, JSON.stringify(knowledge, null, 2), 'utf-8');
  console.log(`Сохранено в ${outputFile}: ${knowledge.length} записей`);
  console.log('\nПример:');
  console.log(JSON.stringify(knowledge.slice(0, 2), null, 2));
}

main().catch(console.error);
