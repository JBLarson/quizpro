// static/js/quiz.js
// Fetch and display hints on demand via /get_hint endpoint
document.addEventListener('DOMContentLoaded', function() {
  const hintBtn = document.getElementById('hint-btn');
  const hintText = document.getElementById('hint-text');
  const questionIdElem = document.getElementById('questionId');
  const questionId = questionIdElem ? questionIdElem.value : null;
  if (hintBtn && hintText && questionId) {
    hintBtn.addEventListener('click', async function() {
      // hide if already visible
      if (hintText.style.display === 'block') {
        hintText.style.display = 'none';
        return;
      }
      // show and fetch hint
      hintText.style.display = 'block';
      hintText.textContent = 'Loading hint…';
      try {
        const res = await fetch('/get_hint', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({question_id: questionId})
        });
        const data = await res.json();
        hintText.textContent = data.hint || 'No hint available.';
      } catch (err) {
        console.error('Error fetching hint:', err);
        hintText.textContent = 'Hint unavailable.';
      }
    });
  }
}); 