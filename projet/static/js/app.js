const navToggle = document.querySelector('.nav-toggle');
const navigation = document.querySelector('.main-nav');

document.querySelectorAll('.report-image img, .admin-report-main img').forEach((image) => {
  image.addEventListener('error', () => {
    image.hidden = true;
    image.parentElement?.classList.add('image-unavailable');
  }, { once: true });
});

navToggle?.addEventListener('click', () => {
  const isOpen = navToggle.getAttribute('aria-expanded') === 'true';
  navToggle.setAttribute('aria-expanded', String(!isOpen));
  navigation?.classList.toggle('is-open', !isOpen);
});

const reportForm = document.querySelector('[data-report-form]');
const photoInput = document.querySelector('[data-photo-input]');
const photoPreview = document.querySelector('[data-photo-preview]');
const photoPreviewImage = photoPreview?.querySelector('img');
const formError = document.querySelector('[data-form-error]');
const descriptionInput = reportForm?.querySelector('[name="description"]');
const characterCount = document.querySelector('[data-character-count]');
let previewUrl;

descriptionInput?.addEventListener('input', () => {
  if (characterCount) characterCount.textContent = `${descriptionInput.value.length} / 1000`;
});

photoInput?.addEventListener('change', () => {
  const file = photoInput.files?.[0];
  if (!file) return;
  if (!['image/jpeg', 'image/png'].includes(file.type) || file.size > 2 * 1024 * 1024) {
    photoInput.value = '';
    if (formError) formError.textContent = 'Choisissez une image JPG ou PNG de 2 Mo maximum.';
    photoPreview.hidden = true;
    return;
  }
  if (formError) formError.textContent = '';
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  if (photoPreviewImage) photoPreviewImage.src = previewUrl;
  if (photoPreview) photoPreview.hidden = false;
});

document.querySelector('[data-clear-photo]')?.addEventListener('click', () => {
  if (photoInput) photoInput.value = '';
  if (photoPreview) photoPreview.hidden = true;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
});

reportForm?.addEventListener('submit', (event) => {
  const file = photoInput?.files?.[0];
  const description = descriptionInput?.value.trim() ?? '';
  if (description.length < 20 || !file || file.size > 2 * 1024 * 1024) {
    event.preventDefault();
    if (formError) formError.textContent = description.length < 20
      ? 'La description doit contenir au moins 20 caractères.'
      : 'Ajoutez une photo JPG ou PNG de 2 Mo maximum.';
  }
});

document.querySelectorAll('.admin-action select[name="statut"]').forEach((select) => {
  select.addEventListener('change', () => {
    const reason = select.closest('form')?.querySelector('.rejection-field input');
    if (reason) reason.required = select.value === 'rejeté';
  });
});