const axios = require('axios'); // npm install axios if not installed

async function runDemo() {
    try {
        // -----------------------------
        // Upload file (encrypt)
        // -----------------------------
        const FormData = require('form-data');
        const fs = require('fs');
        const path = require('path');

        const filePath = path.join(__dirname, 'sample.txt'); // file to encrypt

        const form = new FormData();
        form.append('file', fs.createReadStream(filePath));

        const uploadRes = await axios.post('http://localhost:3000/upload-encrypt', form, {
            headers: form.getHeaders()
        });

        console.log('✅ Upload response:', uploadRes.data);

        // -----------------------------
        // Decrypt file
        // -----------------------------
        const decryptRes = await axios.post('http://localhost:3000/decrypt-file', {
            fileId: 'sample.txt',
            user: {
                id: 'user123',
                name: 'Dr. Harini',
                role: 'Doctor',
                permissions: ['canViewPatients', 'canEditPatients']
            }
        });

        console.log('✅ Decrypt response:');
        console.log(decryptRes.data);

    } catch (err) {
        console.error(err.response ? err.response.data : err.message);
    }
}

runDemo();
