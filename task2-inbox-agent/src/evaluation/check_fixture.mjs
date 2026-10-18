import { readFile } from 'node:fs/promises';
import { classify } from '../email/classify.ts';

const fixture=JSON.parse(await readFile(new URL('../../data/emails.json',import.meta.url),'utf8'));
const incorrect=fixture.emails.filter(email=>classify(`${email.subject}\n${email.body}`)!==email.expectedCategory);
console.log(`Rule baseline: ${fixture.emails.length-incorrect.length}/${fixture.emails.length} expected labels matched.`);
if(incorrect.length){for(const item of incorrect)console.error(`${item.id}: expected ${item.expectedCategory}, got ${classify(item.body)}`);process.exitCode=1;}
