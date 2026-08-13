const fs=require('fs');
const html=fs.readFileSync('C:/Projects/Recursive_Harness_2.0/docs/rating-engine/index.html','utf8');
const js=html.slice(html.lastIndexOf('<script>')+8, html.lastIndexOf('</script>'));
const ids=new Set([...html.matchAll(/id="([^"]+)"/g)].map(m=>m[1]));
function node(tag){const n={tagName:tag,className:'',textContent:'',innerHTML:'',children:[],style:{},
  append:(...c)=>n.children.push(...c), appendChild:c=>n.children.push(c),
  getBoundingClientRect:()=>({width:10,height:10}), set onmousemove(f){}, set onmouseleave(f){}};
  return n;}
const reg={}; ids.forEach(i=>reg['#'+i]=node('div'));
global.document={createElement:node, querySelector:s=>reg[s]||node('div')};
global.window=global; global.innerWidth=1200; global.innerHeight=800;
try{ new Function(js)(); console.log('OK — render executed with no error'); }
catch(e){ console.error('FAIL:', e.message, '\n', e.stack.split('\n').slice(0,4).join('\n')); process.exit(1);}
