const { initKMS, createKey, getDEK, rotateKey } = require('./kms');

async function main() {
  await initKMS();

  const fileId = 'sample.txt';
  console.log('Creating key for', fileId);
  await createKey(fileId);

  console.log('Retrieving DEK for', fileId);
  const dek = await getDEK(fileId);
  console.log('DEK (base64):', dek.toString('base64'));

  console.log('Rotating DEK for', fileId);
  const newDek = await rotateKey(fileId);
  console.log('New DEK (base64):', newDek.toString('base64'));
}

main().catch(console.error);
