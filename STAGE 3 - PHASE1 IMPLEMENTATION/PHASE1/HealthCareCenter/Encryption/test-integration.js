// test-integration.js
const path = require('path');
const storage = require('./storageManager');
const kms = require('./kms');
const encryption = require('./encryption');
const fs = require('fs').promises;

(async () => {
    try {
        console.log('--- Initializing storage & KMS ---');
        await storage.initStorage();
        await kms.initKMS();

        const fileName = 'sample.txt';
        const inputFile = path.join(__dirname, fileName);

        // Step 0: Create sample file if it doesn't exist
        try {
            await fs.access(inputFile);
        } catch {
            await fs.writeFile(inputFile, 'Hello Harini! This is a full integration test.');
            console.log('✔ Sample file created:', inputFile);
        }

        // Step 1: Get storage paths
        const { encPath, metaPath } = storage.getStoragePaths(fileName);

        // Step 2: Encrypt file
        console.log('\n[Encrypting file]');
        await encryption.encryptFile(inputFile, encPath, metaPath);
        console.log('✔ Encrypted file:', encPath);
        console.log('✔ Metadata file:', metaPath);

        // Step 3: Temp decrypted path
        const tempPath = storage.getTempPath(fileName);

        // Step 4: Decrypt file
        console.log('\n[Decrypting file]');
        const decrypted = await encryption.decryptFile(encPath, metaPath, tempPath);
        console.log('✔ Decrypted file saved at:', tempPath);
        console.log('→ Decrypted content:', decrypted.toString());

    } catch (err) {
        console.error('❌ Error:', err);
    }
})();
