/*
 * 歡迎使用 JavaScript 程式碼速記本。
 *
 * 輸入一些 JavaScript，然後按右鍵或從執行選單當中選擇:
 * 1. 執行: 評估反白文字（Ctrl+R），
 * 2. 檢測: 帶出執行結果的物件檢測器（Ctrl+I），或是，
 * 3. 顯示: 在反白區域的後面插入結果作為註解。（Ctrl+L）
 */
function getCSSFeatures(e){
  var eStyle = window.getComputedStyle(e, 'null');
  var color = eStyle.color.match(/\d+(\.\d+)?/g).map(Number);
  if(color.length == 3){
    color.push(1);//convert to rgba format
  }
  console.log(color);
  return {color:color};
}
var element = arguments[0]//temp0;
console.log(getCSSFeatures(element));

/*
Exception: ReferenceError: sStyle is not defined
getCSSFeatures@Scratchpad/4:11:15
@Scratchpad/4:15:1
*/