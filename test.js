const a = require('@justalk/anime-api');
(async () => {
  console.log('no website:', JSON.stringify(await a.stream('naruto shippuden', 387)));
  console.log('CHIA-ANIME:', JSON.stringify(await a.stream('naruto shippuden', 387, {website: 'CHIA-ANIME'})));
})();