const fs = require('fs').promises;
const { decryptFileForUser } = require('./decryptionGateway');

async function runDemo() {
    try {
        // Simulated user
        const user = {
            id: 'user123',
            name: 'Dr. Harini',
            role: 'Doctor',
            permissions: ['canViewPatients', 'canEditPatients']  // must include decrypt permission
        };

        // File ID to decrypt (without extension)
        const fileId = 'sample.txt';

        console.log(`Attempting to decrypt file: ${fileId} for user: ${user.name}`);

        // Call the gateway function
        const { tempPath, plain } = await decryptFileForUser(fileId, user);

        console.log('✔ Decryption successful!');
        console.log('Temporary decrypted file path:', tempPath);
        console.log('Decrypted content:');
        console.log(plain.toString());

        // Optional: delete temp file after test
        await fs.unlink(tempPath);
        console.log('Temporary file deleted.');

    } catch (err) {
        console.error('❌ Decryption failed:', err.message);
    }
}

runDemo();
