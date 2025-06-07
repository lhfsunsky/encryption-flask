// decrypt.js

// 从模板注入的变量，Flask 渲染时替换
const keyBase64 = window.keyBase64 || "{{ key }}"; // 你模板里必须有这段 <script> 定义
const ivHex = window.ivHex || "{{ iv }}";

const viewer = document.getElementById("viewer");
const fileListElem = document.getElementById("file-list");

async function loadFileList() {
  try {
    const res = await fetch('/list');
    if (!res.ok) throw new Error('文件列表加载失败');
    const files = await res.json();

    fileListElem.innerHTML = '';
    files.forEach(file => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = '#';
      a.textContent = file;
      a.onclick = (e) => {
        e.preventDefault();
        previewFile(file);
      };
      li.appendChild(a);
      fileListElem.appendChild(li);
    });
  } catch (err) {
    fileListElem.innerHTML = `<li>加载文件列表出错: ${err.message}</li>`;
  }
}

async function previewFile(filePath) {
  try {
    // 解析密钥和IV
    const keyRaw = Uint8Array.from(atob(keyBase64), c => c.charCodeAt(0));
    const iv = Uint8Array.from(ivHex.match(/.{2}/g).map(h => parseInt(h, 16)));

    const cryptoKey = await crypto.subtle.importKey(
      "raw",
      keyRaw,
      { name: "AES-CBC" },
      false,
      ["decrypt"]
    );

    const res = await fetch(`/file/${filePath}`);
    if (!res.ok) {
      viewer.innerHTML = `<p style="color:red;">文件加载失败: ${res.status}</p>`;
      return;
    }

    const encryptedData = new Uint8Array(await res.arrayBuffer());

    const decryptedBuffer = await crypto.subtle.decrypt(
      { name: "AES-CBC", iv },
      cryptoKey,
      encryptedData
    );

    const decryptedData = new Uint8Array(decryptedBuffer);
    const blob = new Blob([decryptedData]);
    const url = URL.createObjectURL(blob);

    viewer.innerHTML = ''; // 清空

    const lower = filePath.toLowerCase();

    if (lower.endsWith('.mp4.enc')) {
      viewer.innerHTML = `<video controls width="640" src="${url}"></video>`;
    } else if (lower.endsWith('.mp3.enc')) {
      viewer.innerHTML = `<audio controls src="${url}"></audio>`;
    } else if (lower.match(/\.(png|jpg|jpeg)\.enc$/)) {
      viewer.innerHTML = `<img src="${url}" style="max-width:640px;">`;
    } else if (lower.endsWith('.pdf.enc')) {
      viewer.innerHTML = `<iframe src="${url}" width="100%" height="600"></iframe>`;
    } else if (lower.endsWith('.txt.enc')) {
      const text = await blob.text();
      viewer.innerHTML = `<pre style="white-space: pre-wrap;">${escapeHtml(text)}</pre>`;
    } else {
      viewer.innerHTML = `<p>该类型不支持在线预览，<a href="${url}" download>点击下载</a></p>`;
    }
  } catch (e) {
    viewer.innerHTML = `<p style="color:red;">解密失败或文件格式错误，请确认密钥正确且文件未损坏。</p>`;
    console.error(e);
  }
}

// 防止XSS的简单转义函数
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 页面加载时拉取文件列表
window.addEventListener('DOMContentLoaded', loadFileList);
