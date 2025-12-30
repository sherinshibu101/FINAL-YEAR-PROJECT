/**
 * Simple backend connectivity test
 */

async function test() {
  try {
    console.log('Testing backend connectivity...\n');
    
    const response = await fetch('http://localhost:3000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        email: 'admin@hospital.com', 
        password: 'Admin@123' 
      }),
      timeout: 5000
    });

    console.log(`Status: ${response.status}`);
    console.log(`Status Text: ${response.statusText}`);
    
    const data = await response.json();
    console.log('Response:', JSON.stringify(data, null, 2));
    
  } catch (error) {
    console.error('Error:', error.message);
    console.error('Full error:', error);
  }
}

test();
