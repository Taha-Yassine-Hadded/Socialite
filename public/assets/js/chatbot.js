(function(){
  const root = document.getElementById('chatbot-root');
  if (!root) return; // partial not included

  const panel = document.getElementById('cb-panel');
  const btn = document.getElementById('cb-toggle');
  const closeBtn = document.getElementById('cb-close');
  const form = document.getElementById('cb-form');
  const input = document.getElementById('cb-input');
  const list = document.getElementById('cb-messages');

  const KEY = 'cb_history_v1';
  const history = JSON.parse(localStorage.getItem(KEY) || '[]');

  const FAQ = [
    { k: ['publier','photo','poster','image'], a: "Pour publier une photo: Ouvrez la zone de création (bouton +), cliquez sur 'Post', ajoutez votre image, ajoutez une légende, puis Publier." },
    { k: ['trouver','voyageurs','recherche'], a: "Pour trouver des voyageurs: utilisez la barre de recherche en haut. Vous pouvez filtrer par nom, centre d'intérêt ou groupe." },
    { k: ['créer','groupe'], a: "Pour créer un groupe: allez dans 'Groups' (menu Create), cliquez sur 'Create group', renseignez le nom, la description et l'avatar, puis validez." },
    { k: ['voir','notifications'], a: "Vos notifications: cliquez sur l'icône cloche dans l'en-tête pour afficher les dernières activités." },
    { k: ['confidentialité','posts','voir'], a: "Qui peut voir vos posts: selon vos paramètres de confidentialité (public, amis, privé). Vous pouvez modifier cela dans les réglages de profil." },
    { k: ['matching','match'], a: "Le matching: il suggère des connexions selon intérêts, amis communs et interactions récentes." },
    { k: ['rejoindre','voyage','groupe','trip'], a: "Rejoindre un voyage de groupe: ouvrez la page du groupe et cliquez sur 'Join'. Si privé, une approbation peut être requise." },
    { k: ['modifier','profil'], a: "Modifier votre profil: allez sur votre profil, cliquez 'Éditer le profil', modifiez vos informations, puis sauvegardez." },
    { k: ['signaler','problème','bug','support'], a: "Signaler un problème: utilisez le menu d'aide ou contactez le support via la page de contact. Décrivez le contexte et joignez une capture si possible." },
    { k: ['score','confiance','trust'], a: "Score de confiance: un indicateur basé sur l'ancienneté, vérifications, avis reçus et comportement (respect des règles)." }
  ];

  function render(type, text){
    const row = document.createElement('div');
    row.className = 'row';
    const msg = document.createElement('div');
    msg.className = `msg ${type}`;
    msg.textContent = text;
    row.appendChild(msg);
    list.appendChild(row);
    list.scrollTop = list.scrollHeight;
  }

  function saveHistory(){
    const items = Array.from(list.querySelectorAll('.msg')).map(m => ({
      t: m.classList.contains('user') ? 'u' : 'b',
      x: m.textContent
    }));
    localStorage.setItem(KEY, JSON.stringify(items));
  }

  function restore(){
    if (!history.length) {
      setTimeout(() => {
        render('bot', "Besoin d'aide ? 😊 Posez-moi une question (ex: ‘Comment publier une photo ?’) ");
        saveHistory();
      }, 150);
      return;
    }
    history.forEach(h => render(h.t === 'u' ? 'user' : 'bot', h.x));
  }

  function open(){
    panel.hidden = false;
    btn.setAttribute('aria-expanded','true');
    input.focus();
  }
  function close(){
    panel.hidden = true;
    btn.setAttribute('aria-expanded','false');
    btn.focus();
  }

  btn.addEventListener('click', () => {
    if (panel.hidden) open(); else close();
  });
  closeBtn.addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !panel.hidden) close();
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = (input.value || '').trim();
    if (!q) return;
    render('user', q);
    input.value = '';

    const low = q.toLowerCase();
    const found = FAQ.find(f => f.k.some(k => low.includes(k)));
    const ans = found ? found.a : "Désolé, je n'ai pas compris. Essayez: 'Comment publier une photo ?', 'Comment créer un groupe ?', 'Qui peut voir mes posts ?'";
    setTimeout(() => { render('bot', ans); saveHistory(); }, 200);
    saveHistory();
  });

  restore();
})();
