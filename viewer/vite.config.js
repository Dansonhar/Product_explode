import {rm} from 'node:fs/promises';
import {defineConfig} from 'vite';

// Full-resolution reconstruction evidence stays in the working tree and model
// package. The deployed viewer uses lightweight WebP derivatives instead.
export default defineConfig({
  // GitHub Pages serves the site from /<repo>/; local dev stays at /.
  base:process.env.VITE_BASE || '/',
  plugins:[{
    name:'trim-private-review-assets',
    apply:'build',
    async closeBundle(){
      await Promise.all([
        rm('dist/references/brochure',{recursive:true,force:true}),
        rm('dist/renders',{recursive:true,force:true})
      ]);
    }
  }]
});
