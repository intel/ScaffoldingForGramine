const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello, World!');
});

app.listen('/tmp/http.socket', () => {
    console.log('Server is ready');
});
