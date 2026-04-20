const sourceCode = document.getElementById('source-code');
const targetCode = document.getElementById('target-code');
const sourceLang = document.getElementById('source-lang');
const targetLang = document.getElementById('target-lang');
const btnTranslate = document.getElementById('btn-translate');
const btnCopy = document.getElementById('btn-copy');
const btnSample = document.getElementById('btn-sample');
const toast = document.getElementById('error-toast');

const samples = {
    python: `def calculate_sum(limit):
    total = 0
    for i in range(limit):
        if i > 5:
            total = total + i
    print(total)

calculate_sum(10)`,
    java: `public static void calculateSum(int limit) {
    int total = 0;
    for (int i = 0; i < limit; i++) {
        if (i > 5) {
            total = total + i;
        }
    }
    System.out.println(total);
}`,
    "c++": `void calculate_sum(int limit) {
    int total = 0;
    for (int i = 0; i < limit; i++) {
        if (i > 5) {
            total = total + i;
        }
    }
    std::cout << total << std::endl;
}`
};

function showToast(message, isError = true) {
    toast.textContent = message;
    toast.style.background = isError ? 'var(--error-color)' : 'var(--success-color)';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

btnSample.addEventListener('click', () => {
    sourceCode.value = samples[sourceLang.value];
});

sourceLang.addEventListener('change', () => {
    // If empty, load sample automatically
    if (!sourceCode.value.trim()) {
        sourceCode.value = samples[sourceLang.value];
    }
});

btnCopy.addEventListener('click', () => {
    const text = targetCode.textContent;
    if (!text || text.includes('Translation will appear here')) return;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', false);
    }).catch(() => {
        showToast('Failed to copy text.');
    });
});

targetLang.addEventListener('change', () => {
    const lang = targetLang.value === 'c++' ? 'cpp' : targetLang.value;
    targetCode.className = `language-${lang}`;
    Prism.highlightElement(targetCode);
});

btnTranslate.addEventListener('click', async () => {
    const code = sourceCode.value.trim();
    if (!code) {
        showToast('Please enter some code to translate.');
        return;
    }

    if (sourceLang.value === targetLang.value) {
        showToast('Source and Target languages cannot be the same.');
        return;
    }

    const originalText = btnTranslate.innerHTML;
    btnTranslate.innerHTML = 'Translating...';
    btnTranslate.disabled = true;

    try {
        const response = await fetch('/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_code: code,
                source_lang: sourceLang.value,
                target_lang: targetLang.value
            })
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            targetCode.textContent = data.translated_code;
            const langClass = targetLang.value === 'c++' ? 'cpp' : targetLang.value;
            targetCode.className = `language-${langClass}`;
            Prism.highlightElement(targetCode);
        } else {
            showToast(data.message || 'Translation failed.');
        }
    } catch (err) {
        showToast('Network error or server is down.');
    } finally {
        btnTranslate.innerHTML = originalText;
        btnTranslate.disabled = false;
    }
});
