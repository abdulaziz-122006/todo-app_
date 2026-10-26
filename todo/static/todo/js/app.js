// Smart To-Do List - Push Bildirishnomalar va Vaqt Tizimi

// 1. Serverdan kelgan vazifalar ro'yxati
const tasksDataEl = document.getElementById('scheduled-tasks-data');
const scheduledTasks = tasksDataEl ? JSON.parse(tasksDataEl.textContent) : [];

// Mahalliy bildirishnoma berilgan task ID lari
const alertedTaskIds = new Set();
scheduledTasks.forEach(function (t) {
    if (t.notified) {
        alertedTaskIds.add(t.id);
    }
});

// 2. Jonli soat (Live Clock)
function updateLiveClock() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const clockEl = document.getElementById('live-clock');
    if (clockEl) {
        clockEl.textContent = `${hours}:${minutes}:${seconds}`;
    }
}
setInterval(updateLiveClock, 1000);
updateLiveClock();

// 3. Tezkor vaqt kiritish funksiyalari
function formatDateTimeLocal(date) {
    const pad = (n) => String(n).padStart(2, '0');
    const yyyy = date.getFullYear();
    const mm = pad(date.getMonth() + 1);
    const dd = pad(date.getDate());
    const hh = pad(date.getHours());
    const min = pad(date.getMinutes());
    return `${yyyy}-${mm}-${dd}T${hh}:${min}`;
}

function addMinutes(min) {
    const input = document.getElementById('due-date-input');
    if (!input) return;
    let base = new Date();
    if (input.value) {
        const existing = new Date(input.value);
        if (!isNaN(existing.getTime()) && existing > new Date()) {
            base = existing;
        }
    }
    const target = new Date(base.getTime() + min * 60 * 1000);
    input.value = formatDateTimeLocal(target);
    if (typeof updateDueDatePreview === 'function') updateDueDatePreview(target);
    if (typeof highlightDueInput === 'function') highlightDueInput();
}

function setTodayEvening() {
    const input = document.getElementById('due-date-input');
    if (!input) return;
    const target = new Date();
    target.setHours(18, 0, 0, 0);
    if (target < new Date()) {
        target.setDate(target.getDate() + 1);
    }
    input.value = formatDateTimeLocal(target);
    if (typeof updateDueDatePreview === 'function') updateDueDatePreview(target);
    if (typeof highlightDueInput === 'function') highlightDueInput();
}

function setTomorrowMorning() {
    const input = document.getElementById('due-date-input');
    if (!input) return;
    const target = new Date();
    target.setDate(target.getDate() + 1);
    target.setHours(9, 0, 0, 0);
    input.value = formatDateTimeLocal(target);
    if (typeof updateDueDatePreview === 'function') updateDueDatePreview(target);
    if (typeof highlightDueInput === 'function') highlightDueInput();
}

function clearDueDate() {
    const input = document.getElementById('due-date-input');
    if (!input) return;
    input.value = '';
    if (typeof updateDueDatePreview === 'function') updateDueDatePreview(null);
    if (typeof highlightDueInput === 'function') highlightDueInput();
}

// 4. Audio Chime (Web Audio API orqali chiroyli qo'ng'iroq ovozi)
function playChimeSound() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const now = ctx.currentTime;

        // 1-ohang: Do-Re-Mi uslubidagi yoqimli signal (659.25Hz -> 880Hz)
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(659.25, now);
        osc1.frequency.exponentialRampToValueAtTime(880, now + 0.15);
        gain1.gain.setValueAtTime(0.35, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.9);
        osc1.connect(gain1);
        gain1.connect(ctx.destination);
        osc1.start(now);
        osc1.stop(now + 0.9);

        // 2-ohang: Xushovoz aks-sado
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'triangle';
        osc2.frequency.setValueAtTime(880, now + 0.2);
        osc2.frequency.exponentialRampToValueAtTime(1318.5, now + 0.4);
        gain2.gain.setValueAtTime(0.3, now + 0.2);
        gain2.gain.exponentialRampToValueAtTime(0.001, now + 1.4);
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.start(now + 0.2);
        osc2.stop(now + 1.4);
    } catch (err) {
        console.warn('Audio play restricted or unsupported:', err);
    }
}

// 5. In-App Ekranda Chiquvchi Toast Bildirishnoma
function showInAppToast(task) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-popup';
    toast.innerHTML = `
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:8px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:20px;">⏰</span>
                <div>
                    <h4 style="font-size:13px;font-weight:700;color:var(--text-primary);">Vazifa vaqti yetdi!</h4>
                    <p style="font-size:12px;color:var(--text-secondary);margin-top:2px;">${task.title}</p>
                </div>
            </div>
            <button type="button" onclick="this.closest('.toast-popup').remove()" style="background:none;border:none;color:var(--text-tertiary);cursor:pointer;font-size:14px;">✕</button>
        </div>
        <div style="display:flex;align-items:center;gap:8px;padding-top:8px;border-top:1px solid var(--glass-border);">
            <a href="/toggle/${task.id}/" style="flex:1;text-align:center;background:#10b981;color:#fff;font-weight:600;font-size:11.5px;padding:6px 12px;border-radius:10px;text-decoration:none;">
                ✓ Bajarildi
            </a>
            <button type="button" data-task-id="${task.id}" data-minutes="15" onclick="handleSnoozeClick(this); this.closest('.toast-popup').remove();" style="background:var(--glass-bg-subtle);border:1px solid var(--glass-border);color:var(--text-primary);font-size:11.5px;padding:6px 10px;border-radius:10px;cursor:pointer;">
                ⏱️ +15 daqiqa
            </button>
        </div>
    `;
    container.appendChild(toast);

    setTimeout(function () {
        if (toast && toast.parentNode) {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.5s';
            setTimeout(function () {
                toast.remove();
            }, 500);
        }
    }, 15000);
}

// 6. Push Bildirishnoma Yuborish (System Push Notification)
function triggerPushNotification(task) {
    playChimeSound();
    showInAppToast(task);

    if ("Notification" in window && Notification.permission === "granted") {
        const title = "⏰ Vazifa vaqti yetdi!";
        const options = {
            body: `"${task.title}" vazifasini bajarish vaqti bo'ldi.`,
            icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">⏰</text></svg>',
            badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">📌</text></svg>',
            tag: `task-${task.id}`,
            renotify: true,
            requireInteraction: true
        };

        try {
            if (navigator.serviceWorker && navigator.serviceWorker.controller) {
                navigator.serviceWorker.ready.then(function (reg) {
                    reg.showNotification(title, options);
                });
            } else {
                const notif = new Notification(title, options);
                notif.onclick = function () {
                    window.focus();
                    this.close();
                };
            }
        } catch (e) {
            new Notification(title, options);
        }
    }

    markTaskAsNotified(task.id);
}

function markTaskAsNotified(taskId) {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfInput ? csrfInput.value : '';
    fetch(`/mark-notified/${taskId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    }).catch(function (err) {
        console.error("Xatolik notified saqlashda:", err);
    });
}

function handleSnoozeClick(btn) {
    const taskId = btn.getAttribute('data-task-id');
    const minutes = btn.getAttribute('data-minutes') || 15;
    if (taskId) {
        snoozeTask(taskId, minutes);
    }
}

function snoozeTask(taskId, minutes) {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfInput ? csrfInput.value : '';
    const formData = new FormData();
    formData.append('minutes', minutes);

    fetch(`/snooze/${taskId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(function (res) {
        return res.json();
    })
    .then(function (data) {
        if (data.status === 'ok') {
            window.location.reload();
        }
    })
    .catch(function (err) {
        console.error("Snooze xatosi:", err);
    });
}

// 7. Vaqtni tekshiruvchi asosiy mexanizm (Ticker)
function checkTaskDeadlines() {
    const nowSec = Math.floor(Date.now() / 1000);

    scheduledTasks.forEach(function (task) {
        if (task.dueEpochSec && nowSec >= task.dueEpochSec && !alertedTaskIds.has(task.id)) {
            alertedTaskIds.add(task.id);
            task.notified = true;
            triggerPushNotification(task);
        }
    });

    updateAllBadges(nowSec);
}

function updateAllBadges(nowSec) {
    document.querySelectorAll('.due-badge').forEach(function (badge) {
        const epoch = parseInt(badge.getAttribute('data-due-epoch'), 10);
        const isCompleted = badge.getAttribute('data-completed') === 'true';
        if (!epoch || isCompleted) return;

        const diffSec = epoch - nowSec;
        const taskId = badge.id.replace('due-badge-', '');
        const countdownEl = document.getElementById(`countdown-${taskId}`);

        if (diffSec < 0) {
            badge.className = 'due-badge overdue';
            if (countdownEl) {
                const passedMin = Math.abs(Math.floor(diffSec / 60));
                countdownEl.textContent = passedMin > 60 ? `(${Math.floor(passedMin / 60)}s oldin)` : `(${passedMin} daq oldin)`;
            }
        } else if (diffSec <= 15 * 60) {
            badge.className = 'due-badge soon';
            if (countdownEl) {
                const remMin = Math.ceil(diffSec / 60);
                countdownEl.textContent = `(${remMin} daq qoldi)`;
            }
        } else {
            badge.className = 'due-badge';
            if (countdownEl) {
                const remMin = Math.ceil(diffSec / 60);
                if (remMin < 120) {
                    countdownEl.textContent = `(${remMin} daq)`;
                } else {
                    countdownEl.textContent = '';
                }
            }
        }
    });
}

setInterval(checkTaskDeadlines, 3000);
checkTaskDeadlines();

function pollServerForDueTasks() {
    fetch('/api/due-tasks/')
        .then(function (res) {
            return res.json();
        })
        .then(function (data) {
            if (data.tasks && data.tasks.length > 0) {
                data.tasks.forEach(function (task) {
                    if (!alertedTaskIds.has(task.id)) {
                        alertedTaskIds.add(task.id);
                        triggerPushNotification(task);
                    }
                });
            }
        })
        .catch(function (err) {
            console.debug("Server sync:", err);
        });
}
setInterval(pollServerForDueTasks, 30000);

// 8. Bildirishnoma ruxsatini boshqarish
function updateNotifUI() {
    // Intentionally graceful if elements not present in minimal view
}

function enablePushNotifications() {
    if (!("Notification" in window)) {
        alert("Brauzeringizda bildirishnoma qo'llab-quvvatlanmaydi.");
        return;
    }

    Notification.requestPermission().then(function (permission) {
        if (permission === "granted") {
            playChimeSound();
            new Notification("✅ Ruxsat berildi!", {
                body: "Ajoyib! Endi vazifalaringiz vaqti kelganda sizga push bildirishnoma yuboriladi.",
                icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🎉</text></svg>'
            });
        }
    });
}

function sendTestNotification() {
    triggerPushNotification({
        id: 999999,
        title: "Sinov vazifasi: Push bildirishnoma muvaffaqiyatli ishlayapti! 🚀",
        priority: "Yuqori"
    });
}

if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
        navigator.serviceWorker.register('/sw.js').then(function (reg) {
            console.log('ServiceWorker registered with scope:', reg.scope);
        }).catch(function (err) {
            console.log('ServiceWorker registration failed:', err);
        });
    });
}

// 9. Vazifalarni saralash (Tabs filtri)
function filterTasks(type) {
    const buttons = document.querySelectorAll('.filter-tab, .tab-btn');
    buttons.forEach(function (btn) {
        btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`tab-${type}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    const cards = document.querySelectorAll('.task-card');
    cards.forEach(function (card) {
        const isCompleted = card.getAttribute('data-completed') === 'true';
        const hasDue = card.getAttribute('data-has-due') === 'true';

        let show = false;
        if (type === 'all') {
            show = true;
        } else if (type === 'pending') {
            show = !isCompleted;
        } else if (type === 'timed') {
            show = hasDue && !isCompleted;
        } else if (type === 'completed') {
            show = isCompleted;
        }
        card.style.display = show ? '' : 'none';
    });
}
