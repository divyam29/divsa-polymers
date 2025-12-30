// SEO-focused event tracking helpers
document.addEventListener('DOMContentLoaded', function(){
    // Form submits: track and let the form submit normally (the app uses redirect)
    const form = document.getElementById('distributor-form');
    if(form){
        form.addEventListener('submit', function(){
            if(window.gtag){
                gtag('event', 'submit_inquiry', { 'event_category': 'Form', 'event_label': 'Distributor Form'});
            }
        });
    }

    // Track CTA clicks
    document.querySelectorAll('[data-cta-event]').forEach(function(el){
        el.addEventListener('click', function(){
            const label = el.getAttribute('data-cta-event') || 'cta_click';
            if(window.gtag){
                gtag('event', 'click', { 'event_category': 'CTA', 'event_label': label });
            }
        });
    });
});
