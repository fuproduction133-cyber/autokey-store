// AutoKey Store - Main JavaScript

// --- LAUNCHPAD LOADING SCREEN ---
(function() {
    var lp = document.getElementById('launchpad');
    if (!lp) return;
    var minShow = 900;
    var start = Date.now();
    window.addEventListener('load', function() {
        var elapsed = Date.now() - start;
        var wait = Math.max(0, minShow - elapsed);
        setTimeout(function() {
            lp.classList.add('fade-out');
            setTimeout(function() { lp.style.display = 'none'; }, 650);
        }, wait);
    });
})();

// --- REGISTER POPUP ---
function openRegisterPopup() {
    var popup = document.getElementById('registerPopup');
    if (popup) {
        popup.style.display = 'flex';
        var firstInput = popup.querySelector('input[type="text"]');
        if (firstInput) setTimeout(function() { firstInput.focus(); }, 150);
    }
}
function closeRegisterPopup() {
    var popup = document.getElementById('registerPopup');
    if (popup) popup.style.display = 'none';
}

// Auto-open popup if ?popup=1
(function() {
    if (new URLSearchParams(window.location.search).get('popup') === '1') {
        openRegisterPopup();
    }
})();

// --- TERMS MODAL ---
function showTerms() {
    var tm = document.getElementById('termsModal');
    if (tm) {
        tm.style.display = 'flex';
        switchTab('terms');
    }
}
function closeTerms() {
    var tm = document.getElementById('termsModal');
    if (tm) tm.style.display = 'none';
}
function switchTab(tab) {
    var t = document.getElementById('modal-terms');
    var p = document.getElementById('modal-privacy');
    if (t) t.style.display = tab === 'terms' ? 'block' : 'none';
    if (p) p.style.display = tab === 'privacy' ? 'block' : 'none';
    var tb = document.getElementById('tab-terms-btn');
    var pb = document.getElementById('tab-privacy-btn');
    if (tb) tb.classList.toggle('active', tab === 'terms');
    if (pb) pb.classList.toggle('active', tab === 'privacy');
}

document.addEventListener('DOMContentLoaded', function() {
    // Click overlay to close popups
    var termsModal = document.getElementById('termsModal');
    if (termsModal) {
        termsModal.addEventListener('click', function(e) {
            if (e.target === termsModal) closeTerms();
        });
    }
    var regPopup = document.getElementById('registerPopup');
    if (regPopup) {
        regPopup.addEventListener('click', function(e) {
            if (e.target === regPopup) closeRegisterPopup();
        });
    }
    // Escape to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeRegisterPopup();
            closeTerms();
        }
    });
    // Form submit loading state
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var btn = form.querySelector('button[type="submit"]');
            if (btn && !btn.disabled) {
                btn.disabled = true;
                var orig = btn.textContent;
                btn.innerHTML = '<span class="loading"></span> Đang xử lý...';
                setTimeout(function() {
                    if (btn.textContent.includes('Đang xử lý')) {
                        btn.disabled = false;
                        btn.textContent = orig;
                    }
                }, 10000);
            }
        });
    });
});

// Auto-dismiss alerts after 5 seconds
document.querySelectorAll('.alert').forEach(function(alert) {
    setTimeout(function() {
        alert.style.transition = 'opacity 0.5s';
        alert.style.opacity = '0';
        setTimeout(function() { alert.remove(); }, 500);
    }, 5000);
});

// Copy to clipboard
window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(function() {
        var btn = event.target;
        var original = btn.textContent;
        btn.textContent = '✓ Đã sao chép!';
        btn.style.color = 'var(--success)';
        setTimeout(function() {
            btn.textContent = original;
            btn.style.color = '';
        }, 2000);
    });
};

// Keyboard shortcut for copy (Ctrl+C on selected key)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'c') {
        var selection = window.getSelection().toString();
        if (selection.length > 10) {
            navigator.clipboard.writeText(selection);
        }
    }
});
