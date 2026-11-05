// Rebuild with Node.js + @napi-rs/canvas and ffmpeg. Original movie files are read locally.
const fs=require('fs'),path=require('path'),os=require('os'),cp=require('child_process'),crypto=require('crypto');
const {runtime,createCanvas}=require('./canvas-runtime.cjs');
const dir=__dirname,root=process.argv[2]?path.resolve(process.argv[2]):path.resolve(dir,'../../..');
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8'));
const only=process.argv[3];
for(const item of manifest.items){if(only&&item.id!==only)continue;const src=path.join(root,item.sourcePath);const data=fs.readFileSync(src),sha=crypto.createHash('sha1').update(Buffer.concat([Buffer.from('blob '+data.length+'\0'),data])).digest('hex');if(item.sourceBlob&&sha!==item.sourceBlob)throw Error('Source revision mismatch: '+item.sourcePath);
 const {film,canvas}=runtime(src);if(item.kind==='original')film.select(item.originalScene);
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gif-frames-')),count=Math.round((item.end-item.start)*item.fps),c=createCanvas(item.renderSize.width,item.renderSize.height),g=c.getContext('2d');
 for(let i=0;i<count;i++){film.render(item.start+i/item.fps);const kx=canvas.width/item.sourceSize[0],ky=canvas.height/item.sourceSize[1],r=item.crop;g.clearRect(0,0,c.width,c.height);g.drawImage(canvas,r.x*kx,r.y*ky,r.width*kx,r.height*ky,0,0,c.width,c.height);fs.writeFileSync(path.join(temp,String(i).padStart(4,'0')+'.png'),c.toBuffer('image/png'));if(i===Math.floor(count*.45))fs.writeFileSync(path.join(dir,item.poster),c.toBuffer('image/webp'));}
 cp.execFileSync('ffmpeg',['-v','error','-y','-threads','1','-framerate',String(item.fps),'-i',path.join(temp,'%04d.png'),'-filter_complex_threads','1','-filter_complex','[0:v]split[a][b];[a]palettegen=max_colors=256:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle','-loop','0',path.join(dir,item.gif)],{stdio:'inherit'});
 item.bytes=fs.statSync(path.join(dir,item.gif)).size;item.frameCount=count;item.sha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,item.gif))).digest('hex');fs.rmSync(temp,{recursive:true});console.log(item.id+' '+count+' frames '+Math.round(item.bytes/1024)+' KiB');
}
fs.writeFileSync(path.join(dir,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
