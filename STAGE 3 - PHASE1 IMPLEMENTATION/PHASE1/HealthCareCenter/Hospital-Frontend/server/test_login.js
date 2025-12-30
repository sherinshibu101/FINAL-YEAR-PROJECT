const bcrypt = require('bcryptjs');

// Test password
const password = 'Admin@123';
const hash = '$2a$10$LWy57LSmPy4tyBBy6CfMguNX8aCfMLXMR7JtBvwAbpf.N54PX9GmG';

console.log('Testing password:', password);
console.log('Testing hash:', hash);
console.log('Match result:', bcrypt.compareSync(password, hash));

// Also test by reading from users.json
const fs = require('fs');
const users = JSON.parse(fs.readFileSync('./users.json', 'utf8'));
const adminUser = users['admin@hospital.com'];
console.log('\nAdmin user hash:', adminUser.password);
console.log('Password match with admin user:', bcrypt.compareSync(password, adminUser.password));
