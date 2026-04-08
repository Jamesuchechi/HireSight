try {
  console.log('__filename:', __filename);
} catch (e) {
  console.log('__filename not available');
}
try {
  console.log('import.meta.url:', import.meta.url);
} catch (e) {
  console.log('import.meta not available');
}
