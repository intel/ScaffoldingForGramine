const Koa = require("koa");
const app = new Koa();

app.use(async (ctx) => {
        ctx.body = "Hello World";
})

app.listen('/tmp/http.socket', () => {
    console.log('Server is ready');
});
