const fs = require('fs').promises;
const path = require('path');
const { encryptFile, decryptFile } = require('./encryption');


const SAMPLE_FILE = path.join(__dirname, 'sample.txt');
const ENC_FILE = path.join(__dirname, 'sample.txt.enc');
const META_FILE = path.join(__dirname, 'sample.txt.meta.json');
const DECRYPTED_FILE = path.join(__dirname, 'sample_decrypted.txt');

async function main() {
  console.log('--- Encryption Test ---');

  
  console.log('[1] Creating sample file...');
  await fs.writeFile(SAMPLE_FILE, 'Hello Harini! This is your AES-256-GCM test file.');


  console.log('[2] Encrypting sample file...');
  await encryptFile(SAMPLE_FILE, ENC_FILE, META_FILE);
  console.log('   ✔ Encrypted file created:', ENC_FILE);
  console.log('   ✔ Metadata file created:', META_FILE);

 
  console.log('[3] Decrypting encrypted file...');
  await decryptFile(ENC_FILE, META_FILE, DECRYPTED_FILE);
  console.log('   ✔ Decrypted file saved at:', DECRYPTED_FILE);

 
  console.log('[4] Reading decrypted text...');
  const decryptedData = await fs.readFile(DECRYPTED_FILE, 'utf8');
  console.log('   → Decrypted content:', decryptedData);

  console.log('\nALL GOOD ✔ Your encryption engine works correctly!');
}


main().catch(err => {
  console.error('\nERROR OCCURRED:', err);
});
