import {chromium} from '/Users/crave/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const catalog=JSON.parse(await readFile(root+'viewer/public/models/catalog.json','utf8'));
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--enable-webgl','--use-gl=angle','--use-angle=metal']});
const page=await browser.newPage({viewport:{width:1600,height:1000},deviceScaleFactor:1});const errors=[];
page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url())});
await mkdir(root+'review',{recursive:true});
await page.goto('http://127.0.0.1:4180/',{waitUntil:'networkidle'});
await page.locator('#loading').waitFor({state:'hidden'});
let variants=0;
for(let i=0;i<catalog.length;i++){
 await page.locator(`[data-product="${i}"]`).click();await page.locator('#loading').waitFor({state:'hidden'});await page.waitForFunction(()=>document.querySelectorAll('#parts .part').length>0);
 for(let v=0;v<catalog[i].variants.length;v++){
  if(v){await page.selectOption('#variant',String(v));await page.locator('#loading').waitFor({state:'hidden'})}
  variants++;
 }
}
await page.locator('[data-product="5"]').click();await page.locator('#loading').waitFor({state:'hidden'});await page.waitForTimeout(700);await page.screenshot({path:root+'review/flatwise-elbow.png'});
const canvas=page.locator('#canvas');const bounds=await canvas.boundingBox();await page.mouse.move(bounds.x+bounds.width*.55,bounds.y+bounds.height*.48);await page.mouse.down();await page.mouse.move(bounds.x+bounds.width*.68,bounds.y+bounds.height*.38,{steps:8});await page.mouse.up();await page.waitForTimeout(4000);const cameraBefore=await page.evaluate(()=>window.__megaductViewState());
await page.locator('#explode').click();await page.waitForTimeout(1000);await page.screenshot({path:root+'review/flatwise-exploded.png'});
await page.locator('#assemble').click();await page.waitForTimeout(1200);const cameraAfter=await page.evaluate(()=>window.__megaductViewState());const cameraDrift=Math.max(...cameraBefore.map((n,i)=>Math.abs(n-cameraAfter[i])));if(cameraDrift>1e-5)throw Error('Assemble/explode changed the camera view by '+cameraDrift);
await page.locator('#spin').click();await page.waitForTimeout(700);if(!await page.locator('#auto-tour').isVisible()||await page.locator('.tour-callout').count()!==3)throw Error('Automatic detail tour did not create its callouts');await page.screenshot({path:root+'review/auto-detail-tour.png'});await page.locator('#spin').click();if(await page.locator('#auto-tour').isVisible())throw Error('Automatic detail tour did not close');
await page.locator('#parts .part').first().click();await page.locator('#showall').click();await page.locator('#ghost').click();await page.locator('#ghost').click();
await page.locator('[data-product="19"]').click();await page.locator('#loading').waitFor({state:'hidden'});await page.locator('#explode').click();await page.waitForTimeout(1000);await page.screenshot({path:root+'review/joint-exploded.png'});
await page.locator('[data-product="23"]').click();await page.locator('#loading').waitFor({state:'hidden'});await page.waitForTimeout(700);
if(!await page.locator('#flow-story').isVisible()||!await page.locator('#flow-toggle').isVisible())throw Error('Connected-system energy-flow explainer is not visible');
const flowStage=await page.locator('#flow-stage').textContent();await page.waitForTimeout(6800);if(await page.locator('#flow-stage').textContent()===flowStage)throw Error('Connected-system explainer stage did not advance after its reading interval');
await page.locator('#flow-toggle').click();if(await page.locator('#flow-toggle').textContent()!=='Resume energy flow')throw Error('Energy-flow pause control failed');await page.locator('#flow-toggle').click();
await page.screenshot({path:root+'review/connected-system-flow.png'});
const systemDownload=page.waitForEvent('download');await page.locator('#export').click();const systemFile=await systemDownload;await systemFile.saveAs(root+'review/connected-system-download-test.glb');if(!systemFile.suggestedFilename().includes('connected-system'))throw Error('Connected-system export used the wrong filename');
await page.locator('[data-product="15"]').click();await page.locator('#loading').waitFor({state:'hidden'});await page.selectOption('#variant','4');await page.locator('#loading').waitFor({state:'hidden'});await page.waitForTimeout(700);await page.screenshot({path:root+'review/tap-off-rotary.png'});
await page.locator('#reference-open').click();if(!await page.locator('#reference-dialog').isVisible())throw Error('Reference dialog failed');await page.locator('#reference-close').click();
await page.selectOption('#material','aluminium');const download=page.waitForEvent('download');await page.locator('#export').click();const file=await download;await file.saveAs(root+'review/download-test.glb');
await page.setViewportSize({width:390,height:844});await page.waitForTimeout(400);if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Mobile horizontal overflow');await page.locator('#spin').click();await page.waitForTimeout(500);if(await page.locator('.tour-callout:visible').count()!==1)throw Error('Mobile detail tour should show one callout');await page.screenshot({path:root+'review/auto-detail-tour-mobile.png',fullPage:true});await page.locator('#spin').click();await page.screenshot({path:root+'review/mobile.png',fullPage:true});
await page.locator('[data-product="23"]').click();await page.locator('#loading').waitFor({state:'hidden'});await page.waitForTimeout(500);if(!await page.locator('#flow-story').isVisible()||await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Mobile connected-system explainer failed');await page.screenshot({path:root+'review/connected-system-flow-mobile.png',fullPage:true});
await browser.close();const result={families:catalog.length,variants,errors,download:file.suggestedFilename()};await writeFile(root+'review/browser-check.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));if(errors.length)process.exitCode=1;
