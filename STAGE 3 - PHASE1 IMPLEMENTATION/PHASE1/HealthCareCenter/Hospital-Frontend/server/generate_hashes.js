const bcrypt = require('bcryptjs');

const passwords = {
  'Admin@123': null,
  'Doctor@123': null,
  'Nurse@123': null,
  'Reception@123': null
};

Object.keys(passwords).forEach(pwd => {
  passwords[pwd] = bcrypt.hashSync(pwd, 10);
  console.log(`"${pwd}": "${passwords[pwd]}"`);
});
