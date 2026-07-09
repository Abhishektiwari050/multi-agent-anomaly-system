import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function compilePDF() {
  console.log('Launching headless browser...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  const htmlPath = 'file://' + path.resolve(__dirname, 'agent-b-writeup.html');
  console.log(`Loading local HTML file: ${htmlPath}`);
  
  await page.goto(htmlPath, { waitUntil: 'networkidle' });
  
  const outputFileName = 'clinical-execution-agent-submission.pdf';
  const localPDFPath = path.resolve(__dirname, outputFileName);
  
  console.log('Generating high-fidelity A4 PDF write-up...');
  await page.pdf({
    path: localPDFPath,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>', // hide default header
    footerTemplate: '<div style="font-size:8px; width: 100%; display: flex; justify-content: space-between; padding: 0 20mm; color: #94a3b8; font-family: \'Plus Jakarta Sans\', sans-serif; font-weight: 500;"><span>Abhishek Tiwari, Developer</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>',
    margin: { top: '20mm', right: '20mm', bottom: '25mm', left: '20mm' }
  });
  
  console.log(`PDF Generated successfully at ${localPDFPath}`);
  await browser.close();

  // Project destination path
  const projectDestDir = 'C:/Users/abhis/.gemini/antigravity/scratch/multi-agent-anomaly-system/design-writeup';
  const projectDestPath = path.join(projectDestDir, outputFileName);
  
  // Artifacts destination path
  const artifactsDestDir = 'C:/Users/abhis/.gemini/antigravity/brain/9b3f958e-8ad5-425d-ae57-e24b1ca25068';
  const artifactsDestPath = path.join(artifactsDestDir, outputFileName);

  // Copy to destinations
  console.log('Copying PDF to destinations...');
  
  fs.mkdirSync(projectDestDir, { recursive: true });
  fs.copyFileSync(localPDFPath, projectDestPath);
  console.log(`Copied to project folder: ${projectDestPath}`);
  
  fs.mkdirSync(artifactsDestDir, { recursive: true });
  fs.copyFileSync(localPDFPath, artifactsDestPath);
  console.log(`Copied to artifacts folder: ${artifactsDestPath}`);
}

compilePDF().catch(err => {
  console.error('Compilation failed:', err);
  process.exit(1);
});
