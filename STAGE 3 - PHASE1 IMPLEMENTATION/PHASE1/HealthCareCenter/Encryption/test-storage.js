const path = require('path');
const fs = require('fs').promises;
const { initStorage, storeEncryptedFile } = require('./storageManager');

async function main() {
  await initStorage();

  
  const encFile = path.join(__dirname, 'sample.txt.enc');
  const metaFile = path.join(__dirname, 'sample.txt.meta.json');

  const { encPath, metaPath } = await storeEncryptedFile(encFile, metaFile);
  console.log('Encrypted file moved to:', encPath);
  console.log('Metadata file moved to:', metaPath);
}

main().catch(console.error);
