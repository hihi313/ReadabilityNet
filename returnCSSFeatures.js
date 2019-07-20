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
  //color
  var color = eStyle.color.match(/\d+(\.\d+)?/g).map(Number);
  if(color.length == 3){
    color.push(1);//convert to rgba format
  }
  //text-align
  var textAlign = [], tmp = eStyle.textAlign;
  switch(tmp){
    case "left":
      textAlign = [1, 0, 0, 0];
    case "right":
      textAlign = [0, 1, 0, 0];
    case "center":
      textAlign = [0, 0, 1, 0];
    case "justify":
      textAlign = [0, 0, 0, 1];
    default:
      textAlign = NaN;
  }
  return {color:color, textAlign:textAlign};
}
var element = temp0;//arguments[0]
tmp = getCSSFeatures(element);
console.log(tmp);
//return tmp;