
document.addEventListener('DOMContentLoaded', () => {

  // ── Auto-dismiss toasts ──────────────────────────────────────
  document.querySelectorAll('.toast.show').forEach(el => {
    setTimeout(() => {
      const toast = bootstrap.Toast.getOrCreateInstance(el);
      toast.hide();
    }, 4000);
  });

  // ── Star Rating Picker ──────────────────────────────────────
  const starPicker = document.getElementById('starPicker');
  if (starPicker) {
    const url      = starPicker.dataset.url;
    const csrf     = starPicker.dataset.csrf;
    let current    = parseInt(starPicker.dataset.current) || 0;
    const btns     = starPicker.querySelectorAll('.star-btn');
    const avgNum   = document.getElementById('avgRatingNum');
    const avgStars = document.getElementById('avgStars');
    const countTxt = document.getElementById('ratingCountText');

    function renderStars(active) {
      btns.forEach((btn, i) => {
        const filled = i < active;
        btn.classList.toggle('star-active', filled);
        btn.querySelector('i').className = filled ? 'fas fa-star' : 'far fa-star';
      });
    }

    renderStars(current);

    btns.forEach((btn, i) => {
      btn.addEventListener('mouseenter', () => renderStars(i + 1));
      btn.addEventListener('mouseleave', () => renderStars(current));
      btn.addEventListener('click', async () => {
        const stars = i + 1;
        try {
          const res = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrf,
            },
            body: JSON.stringify({ stars }),
          });
          const data = await res.json();
          if (data.success) {
            current = data.user_rating;
            renderStars(current);
            if (avgNum) avgNum.textContent = data.avg_rating;
            if (countTxt) {
              countTxt.textContent = `${data.rating_count} rating${data.rating_count !== 1 ? 's' : ''}`;
            }
            if (avgStars) renderAvgStars(avgStars, data.avg_rating);
            showToast('Rating saved!', 'success');
          }
        } catch {
          showToast('Could not save rating.', 'error');
        }
      });
    });



     
    function renderAvgStars(container, avg) {
      container.innerHTML = '';
      for (let i = 1; i <= 5; i++) {
        const icon = document.createElement('i');
        if (i <= Math.floor(avg)) {
          icon.className = 'fas fa-star star-filled';
        } else if (i - 0.5 <= avg) {
          icon.className = 'fas fa-star-half-stroke star-half';
        } else {
          icon.className = 'far fa-star star-empty';
        }
        container.appendChild(icon);
      }
    }
  }


  const favBtn = document.getElementById('favBtn');
  if (favBtn) {
    favBtn.addEventListener('click', async () => {
      try {
        const res = await fetch(favBtn.dataset.url, {
          method: 'POST',
          headers: { 'X-CSRFToken': favBtn.dataset.csrf },
        });
        const data = await res.json();
        if (data.success) {
          const isFav = data.is_favourite;
          favBtn.innerHTML = isFav
            ? '<i class="fas fa-heart me-2 text-danger"></i>Saved to Favourites'
            : '<i class="far fa-heart me-2"></i>Save to Favourites';
          showToast(isFav ? 'Added to favourites!' : 'Removed from favourites.', 'success');
        }
      } catch {
        showToast('Could not update favourites.', 'error');
      }
    });
  }

  const commentForm = document.getElementById('commentForm');
  if (commentForm) {
    commentForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = commentForm.querySelector('textarea[name="text"]').value.trim();
      if (!text) return;

      try {
        const fd = new FormData(commentForm);
        const res = await fetch(commentForm.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          body: fd,
        });
        const data = await res.json();
        if (data.success) {
          commentForm.querySelector('textarea').value = '';
          appendComment(data.comment);
          document.getElementById('noComments')?.remove();
          showToast('Comment posted!', 'success');
        }
      } catch {
        showToast('Could not post comment.', 'error');
      }
    });
  }

  function appendComment(c) {
    const list = document.getElementById('commentsList');
    const div = document.createElement('div');
    div.className = 'comment-item';
    div.id = `comment-${c.id}`;
    div.innerHTML = `
      <div class="comment-header">
        <span class="comment-author"><i class="fas fa-user-circle me-1"></i>${escapeHtml(c.username)}</span>
        <span class="comment-date">${escapeHtml(c.created_at)}</span>
      </div>
      <p class="comment-text">${escapeHtml(c.text)}</p>`;
    list.insertBefore(div, list.firstChild);
  }

  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.btn-delete-comment');
    if (!btn) return;
    if (!confirm('Delete this comment?')) return;
    try {
      const res = await fetch(btn.dataset.url, {
        method: 'POST',
        headers: { 'X-CSRFToken': btn.dataset.csrf, 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById(`comment-${btn.dataset.commentId}`)?.remove();
        showToast('Comment deleted.', 'success');
      }
    } catch {
      showToast('Could not delete comment.', 'error');
    }
  });

   
  const ingredientsContainer = document.getElementById('ingredientsContainer');
  const addIngredientBtn     = document.getElementById('addIngredient');

  if (ingredientsContainer && addIngredientBtn) {
    addIngredientBtn.addEventListener('click', () => addIngredientRow());

    function addIngredientRow(name = '', amount = '') {
      const row = document.createElement('div');
      row.className = 'ingredient-row';
      row.innerHTML = `
        <div class="row g-2 align-items-center">
          <div class="col">
            <input type="text" name="ingredient_name[]"
                   class="form-control ingredient-name-input"
                   value="${escapeHtml(name)}"
                   placeholder="Ingredient name" autocomplete="off">
          </div>
          <div class="col-4">
            <input type="text" name="ingredient_amount[]"
                   class="form-control"
                   value="${escapeHtml(amount)}"
                   placeholder="Amount (e.g. 50ml)">
          </div>
          <div class="col-auto">
            <button type="button" class="btn btn-outline-danger btn-sm remove-ingredient" title="Remove">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        <div class="autocomplete-dropdown d-none"></div>`;
      ingredientsContainer.appendChild(row);
      attachIngredientListeners(row);
      row.querySelector('.ingredient-name-input').focus();
    }

    document.querySelectorAll('.ingredient-row').forEach(attachIngredientListeners);

    function attachIngredientListeners(row) {
      const removeBtn = row.querySelector('.remove-ingredient');
      if (removeBtn) {
        removeBtn.addEventListener('click', () => {
          if (ingredientsContainer.querySelectorAll('.ingredient-row').length > 1) {
            row.remove();
          } else {
            row.querySelector('.ingredient-name-input').value = '';
            row.querySelector('input[name="ingredient_amount[]"]').value = '';
          }
        });
      }

      const nameInput   = row.querySelector('.ingredient-name-input');
      const acDropdown  = row.querySelector('.autocomplete-dropdown');
      if (!nameInput || !acDropdown || !window.INGREDIENT_AUTOCOMPLETE_URL) return;

      let debounceTimer;
      nameInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => fetchSuggestions(nameInput.value, acDropdown, nameInput), 250);
      });

      nameInput.addEventListener('blur', () => {
        setTimeout(() => acDropdown.classList.add('d-none'), 200);
      });
    }

    async function fetchSuggestions(q, dropdown, input) {
      if (q.length < 2) { dropdown.classList.add('d-none'); return; }
      try {
        const res  = await fetch(`${window.INGREDIENT_AUTOCOMPLETE_URL}?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        if (!data.results.length) { dropdown.classList.add('d-none'); return; }
        dropdown.innerHTML = data.results
          .map(r => `<div class="autocomplete-item" data-name="${escapeHtml(r.name)}">${escapeHtml(r.name)}</div>`)
          .join('');
        dropdown.classList.remove('d-none');
        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
          item.addEventListener('mousedown', () => {
            input.value = item.dataset.name;
            dropdown.classList.add('d-none');
          });
        });
      } catch { dropdown.classList.add('d-none'); }
    }
  }

  const imageInput = document.querySelector('input[type="file"][accept="image/*"]');
  const previewBox = document.getElementById('imagePreview');
  const previewImg = document.getElementById('previewImg');
  if (imageInput && previewBox && previewImg) {
    imageInput.addEventListener('change', () => {
      const file = imageInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = e => {
          previewImg.src = e.target.result;
          previewBox.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
      } else {
        previewBox.classList.add('d-none');
      }
    });
  }

   
  document.querySelectorAll('.toggle-password').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.closest('.input-group').querySelector('input');
      if (!input) return;
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      btn.querySelector('i').className = isPassword ? 'fas fa-eye-slash' : 'fas fa-eye';
    });
  });

  function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container')
      || createToastContainer();

    const toast = document.createElement('div');
    const icon = type === 'success' ? 'fa-circle-check'
               : type === 'error'   ? 'fa-circle-xmark'
               : 'fa-circle-info';

    toast.className = `toast show align-items-center site-toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          <i class="fas ${icon} me-2"></i>${escapeHtml(message)}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function createToastContainer() {
    const c = document.createElement('div');
    c.className = 'toast-container position-fixed top-0 end-0 p-3';
    c.style.zIndex = '1100';
    c.style.marginTop = '80px';
    document.body.appendChild(c);
    return c;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str)));
    return div.innerHTML;
  }

  const mobileToggle = document.getElementById('mobileToggle');
  const mobileMenu   = document.getElementById('mobileMenu');
  if (mobileToggle && mobileMenu) {
    mobileToggle.addEventListener('click', () => {
      mobileMenu.classList.toggle('d-none');
    });
  }

  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', e => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
    });
  });

});
