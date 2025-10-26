// On page load or when changing themes, best to add inline in `head` to avoid FOUC
if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark')
    } else {
    document.documentElement.classList.remove('dark')
    }

// Whenever the user explicitly chooses light mode
localStorage.theme = 'light'

// Whenever the user explicitly chooses dark mode
localStorage.theme = 'dark'

// Whenever the user explicitly chooses to respect the OS preference
localStorage.removeItem('theme')



// add post upload image (guard for pages without this input)
const addPostUrlEl = document.getElementById('addPostUrl');
if (addPostUrlEl) {
  addPostUrlEl.addEventListener('change', function(){
    if (this.files && this.files[0]) {
      var picture = new FileReader();
      picture.readAsDataURL(this.files[0]);
      picture.addEventListener('load', function(event) {
        const img = document.getElementById('addPostImage');
        if (img) {
          img.setAttribute('src', event.target.result);
          img.style.display = 'block';
        }
      });
    }
  });
}


// Create Status upload image (guard)
const createStatusUrlEl = document.getElementById('createStatusUrl');
if (createStatusUrlEl) {
  createStatusUrlEl.addEventListener('change', function(){
    if (this.files && this.files[0]) {
      var picture = new FileReader();
      picture.readAsDataURL(this.files[0]);
      picture.addEventListener('load', function(event) {
        const img = document.getElementById('createStatusImage');
        if (img) {
          img.setAttribute('src', event.target.result);
          img.style.display = 'block';
        }
      });
    }
  });
}


// create product upload image (guard)
const createProductUrlEl = document.getElementById('createProductUrl');
if (createProductUrlEl) {
  createProductUrlEl.addEventListener('change', function(){
    if (this.files && this.files[0]) {
      var picture = new FileReader();
      picture.readAsDataURL(this.files[0]);
      picture.addEventListener('load', function(event) {
        const img = document.getElementById('createProductImage');
        if (img) {
          img.setAttribute('src', event.target.result);
          img.style.display = 'block';
        }
      });
    }
  });
}







    