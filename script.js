const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('resume-file');
const fileNameDisplay = document.getElementById('file-name');

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = `Selected: ${fileInput.files[0].name}`;
    }
});

async function processAnalysis() {
    const jdText = document.getElementById('jd-text').value;
    const resumeText = document.getElementById('resume-text').value;
    const file = fileInput.files[0];

    if (!jdText) {
        alert("Please paste a Job Description.");
        return;
    }

    if (!file && !resumeText) {
        alert("Please upload a PDF resume or paste resume text.");
        return;
    }

    const analyzeBtn = document.getElementById('analyze-btn');
    analyzeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';

    const formData = new FormData();
    formData.append('job_description', jdText);
    if (file) formData.append('resume_file', file);
    if (resumeText) formData.append('resume_text', resumeText);

    try {
        // Local FastAPI server URL
        const response = await fetch('http://127.0.0.1:8000/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        updateResultsUI(data);
    } catch (error) {
        alert("Failed to connect to backend server. Make sure FastAPI is running!");
    } finally {
        analyzeBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run AI Analysis';
    }
}

function updateResultsUI(data) {
    const scoreCircle = document.getElementById('score-circle');
    const scoreStatus = document.getElementById('score-status');
    const matchedWrapper = document.getElementById('matched-tags');
    const missingWrapper = document.getElementById('missing-tags');

    scoreCircle.textContent = `${data.score}%`;
    
    if (data.score >= 70) {
        scoreCircle.style.borderColor = '#4ade80';
        scoreStatus.textContent = "Strong Match!";
        scoreStatus.style.color = '#4ade80';
    } else if (data.score >= 40) {
        scoreCircle.style.borderColor = '#facc15';
        scoreStatus.textContent = "Moderate Match";
        scoreStatus.style.color = '#facc15';
    } else {
        scoreCircle.style.borderColor = '#f87171';
        scoreStatus.textContent = "Low Match";
        scoreStatus.style.color = '#f87171';
    }

    matchedWrapper.innerHTML = data.matched_skills.length > 0 
        ? data.matched_skills.map(s => `<span class="tag tag-success">${s}</span>`).join('')
        : '<span class="placeholder-text">No matching skills found.</span>';

    missingWrapper.innerHTML = data.missing_skills.length > 0 
        ? data.missing_skills.map(s => `<span class="tag tag-danger">${s}</span>`).join('')
        : '<span class="placeholder-text">No missing skills detected!</span>';
}