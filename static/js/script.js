const dropZone      = document.getElementById('dropZone');
const fileInput     = document.getElementById('fileInput');
const fileSelected  = document.getElementById('fileSelected');
const fileName      = document.getElementById('fileName');
const fileSize      = document.getElementById('fileSize');
const fileTypeIcon  = document.getElementById('fileTypeIcon');
const fileRemove    = document.getElementById('fileRemove');
const submitBtn     = document.getElementById('submitBtn');
const btnLabel      = document.getElementById('btnLabel');
const progressWrap  = document.getElementById('progressWrap');
const progressFill  = document.getElementById('progressFill');
const progressText  = document.getElementById('progressText');
const progressPct   = document.getElementById('progressPct');
const resultBox     = document.getElementById('resultBox');
const errorBanner   = document.getElementById('errorBanner');
const errorMsg      = document.getElementById('errorMsg');

const typeIcons = { pdf:'📑', png:'🖼️', jpg:'🖼️', jpeg:'🖼️', tiff:'📸', bmp:'📸' };

function formatBytes(b) {
    if (b < 1024)    return b + ' B';
    if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
    return (b / 1048576).toFixed(1) + ' MB';
}

function showFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    fileTypeIcon.textContent = typeIcons[ext] || '📄';
    fileSelected.classList.add('show');
    dropZone.style.opacity = '0.6';
    dropZone.style.pointerEvents = 'none';
}

function clearFile() {
    fileInput.value = '';
    fileSelected.classList.remove('show');
    dropZone.style.opacity = '1';
    dropZone.style.pointerEvents = '';
}

function setLoading(on) {
    submitBtn.disabled = on;
    submitBtn.innerHTML = on
        ? `<span class="spinner"></span><span>Processing…</span>`
        : `<svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0;">
               <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
           </svg>
           <span>Extract Text with AI</span>
           <svg class="arrow-icon" viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;margin-left:auto;flex-shrink:0;">
               <line x1="5" y1="12" x2="19" y2="12"/>
               <polyline points="12 5 19 12 12 19"/>
           </svg>`;
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorBanner.classList.add('show');
}

function hideError() {
    errorBanner.classList.remove('show');
}

function setProgress(pct, label) {
    progressFill.style.width = pct + '%';
    progressText.textContent = label;
    progressPct.textContent  = pct + '%';
}

function fillResult(data) {
    const d = data.data;

    const dates   = Array.isArray(d.dates)   ? d.dates.join(', ')   : (d.dates || '');
    const amounts = Array.isArray(d.amounts) ? d.amounts.join(', ') : (d.amounts || '');

    function set(id, value) {
        const el = document.getElementById(id);
        if (value && value.trim() !== '') {
            el.textContent = value;
            el.classList.remove('none');
        } else {
            el.textContent = 'None found';
            el.classList.add('none');
        }
    }

    set('resDate',   dates);
    set('resAmount', amounts);
    set('resEmail',  d.email || '');
    set('resText',   d.raw_text || '');

    resultBox.classList.add('show');
}

// ── File input via click ──────────────────────────────
fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) showFile(fileInput.files[0]);
});

fileRemove.addEventListener('click', clearFile);

// ── Drag & drop ───────────────────────────────────────
dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) {
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        showFile(file);
    }
});

// ── Form submit (single listener) ────────────────────
document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) return;

    // Reset previous state
    hideError();
    resultBox.classList.remove('show');
    setLoading(true);
    progressWrap.classList.add('show');
    setProgress(0, 'Uploading document…');

    // Simulated progress steps that run alongside the real fetch
    const steps = [
        { pct: 20, text: 'Uploading document…' },
        { pct: 45, text: 'Preprocessing image…' },
        { pct: 65, text: 'Running OCR engine…' },
        { pct: 85, text: 'Applying NLP analysis…' },
    ];
    let stepIdx = 0;
    const progressInterval = setInterval(() => {
        if (stepIdx < steps.length) {
            setProgress(steps[stepIdx].pct, steps[stepIdx].text);
            stepIdx++;
        }
    }, 600);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/extract', {
            method: 'POST',
            body: formData,
        });

        clearInterval(progressInterval);

        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        setProgress(100, 'Done!');

        if (data.status === 'success') {
            fillResult(data);
        } else {
            showError(data.error || 'Extraction failed. Please try again.');
        }

    } catch (err) {
        clearInterval(progressInterval);
        setProgress(0, '');
        progressWrap.classList.remove('show');
        showError(err.message || 'Something went wrong. Please try again.');
    } finally {
        setLoading(false);
    }
});