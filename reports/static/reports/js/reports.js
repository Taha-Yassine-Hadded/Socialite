document.addEventListener('DOMContentLoaded', function() {
    // Gestion des formulaires de mise à jour de statut
    const updateForms = document.querySelectorAll('form[action*="update/"]');
    updateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Recharger la page pour voir les changements
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
            });
        });
    });
    
    // Gestion des formulaires de suppression
    const deleteForms = document.querySelectorAll('form[action*="delete/"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Êtes-vous sûr de vouloir supprimer ce contenu ?')) {
                e.preventDefault();
                return false;
            }
            
            // La soumission du formulaire se fera normalement
            return true;
        });
    });
});
