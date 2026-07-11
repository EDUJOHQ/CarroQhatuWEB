(function ($) {
    "use strict";
    
    // Dropdown on mouse hover
    $(document).ready(function () {
        function toggleNavbarMethod() {
            if ($(window).width() > 992) {
                $('.navbar .dropdown').on('mouseover', function () {
                    $('.dropdown-toggle', this).trigger('click');
                }).on('mouseout', function () {
                    $('.dropdown-toggle', this).trigger('click').blur();
                });
            } else {
                $('.navbar .dropdown').off('mouseover').off('mouseout');
            }
        }
        toggleNavbarMethod();
        $(window).resize(toggleNavbarMethod);
    });

    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 100) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });


    // Team carousel
    $(".team-carousel, .related-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        center: true,
        margin: 30,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="fa fa-angle-left" aria-hidden="true"></i>',
            '<i class="fa fa-angle-right" aria-hidden="true"></i>'
        ],
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:3
            }
        }
    });

    // Testimonials carousel
    $(".testimonial-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        margin: 30,
        dots: true,
        loop: true,
        center: true,
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:3
            }
        }
    });


    // Vendor carousel
    $('.vendor-carousel').owlCarousel({
        loop: true,
        margin: 30,
        dots: true,
        loop: true,
        center: true,
        autoplay: true,
        smartSpeed: 1000,
        responsive: {
            0:{
                items:2
            },
            576:{
                items:3
            },
            768:{
                items:4
            },
            992:{
                items:5
            },
            1200:{
                items:6
            }
        }
    });

    // Chatbot Inteligente de Atención al Cliente (Asistente Virtual 24/7)
    $(document).ready(function () {
        // Inyectar estilos CSS del Chatbot
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                #cq-chatbot-container {
                    position: fixed;
                    bottom: 100px;
                    right: 30px;
                    z-index: 9999;
                    font-family: 'Rubik', sans-serif;
                }
                #cq-chatbot-trigger {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background-color: #fbd333;
                    color: #0b0f19;
                    border: none;
                    cursor: pointer;
                    box-shadow: 0 4px 15px rgba(251, 211, 51, 0.4);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                    transition: all 0.3s ease;
                }
                #cq-chatbot-trigger:hover {
                    transform: scale(1.05);
                    box-shadow: 0 6px 20px rgba(251, 211, 51, 0.6);
                }
                #cq-chatbot-window {
                    position: absolute;
                    bottom: 80px;
                    right: 0;
                    width: 350px;
                    height: 480px;
                    background-color: #0b0f19;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                    transition: all 0.3s ease;
                }
                .cq-chatbot-header {
                    background-color: #1e293b;
                    padding: 12px 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }
                .cq-chatbot-avatar {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background-color: #fbd333;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.1rem;
                }
                .cq-pulse-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background-color: #10b981;
                    display: inline-block;
                    box-shadow: 0 0 8px #10b981;
                    animation: cq-pulse 2s infinite;
                }
                @keyframes cq-pulse {
                    0% { transform: scale(0.95); opacity: 0.8; }
                    50% { transform: scale(1.1); opacity: 1; }
                    100% { transform: scale(0.95); opacity: 0.8; }
                }
                #cq-chatbot-messages {
                    flex-grow: 1;
                    padding: 15px;
                    overflow-y: auto;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    background-color: #0f172a;
                }
                .cq-msg {
                    max-width: 85%;
                    padding: 10px 14px;
                    border-radius: 12px;
                    font-size: 0.85rem;
                    line-height: 1.4;
                    word-wrap: break-word;
                }
                .cq-msg.assistant {
                    background-color: #1e293b;
                    color: #f8fafc;
                    align-self: flex-start;
                    border-top-left-radius: 2px;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                }
                .cq-msg.user {
                    background-color: #fbd333;
                    color: #0b0f19;
                    font-weight: 500;
                    align-self: flex-end;
                    border-top-right-radius: 2px;
                }
                .cq-chatbot-input-area {
                    padding: 12px 15px;
                    background-color: #1e293b;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }
                #cq-chatbot-input {
                    flex-grow: 1;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    background-color: #0f172a;
                    color: #fff;
                    border-radius: 20px;
                    padding: 8px 15px;
                    font-size: 0.85rem;
                    outline: none;
                }
                #cq-chatbot-input::placeholder {
                    color: #94a3b8;
                }
                #cq-chatbot-input:focus {
                    border-color: #fbd333;
                }
                #cq-chatbot-form button {
                    background-color: #fbd333;
                    color: #0b0f19;
                    border: none;
                    border-radius: 50%;
                    width: 34px;
                    height: 34px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                #cq-chatbot-form button:hover {
                    background-color: #f5c400;
                    transform: scale(1.05);
                }
                .cq-typing {
                    display: flex;
                    gap: 4px;
                    padding: 4px 8px;
                    align-items: center;
                }
                .cq-typing span {
                    width: 6px;
                    height: 6px;
                    background-color: #94a3b8;
                    border-radius: 50%;
                    animation: cq-bounce 1.3s infinite;
                }
                .cq-typing span:nth-child(2) { animation-delay: 0.15s; }
                .cq-typing span:nth-child(3) { animation-delay: 0.3s; }
                @keyframes cq-bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-4px); }
                }
            `)
            .appendTo('head');

        // Inyectar la estructura HTML del Chatbot
        const chatbotHtml = `
            <div id="cq-chatbot-container">
                <div id="cq-chatbot-window">
                    <div class="cq-chatbot-header">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="cq-chatbot-avatar">🤖</div>
                            <div>
                                <h6 style="margin: 0; color: #fff; font-weight: 600; font-size: 0.95rem;">Asesor IA CarroQhatu</h6>
                                <small style="color: #10b981; font-size: 0.75rem; display: flex; align-items: center; gap: 4px;">
                                    <span class="cq-pulse-dot"></span> En línea
                                </small>
                            </div>
                        </div>
                        <button id="cq-chatbot-close" style="background: none; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer;">&times;</button>
                    </div>
                    <div id="cq-chatbot-messages">
                        <div class="cq-msg assistant">
                            <p style="margin:0;">¡Hola! Soy tu Asesor Automotriz de CarroQhatu. Escríbeme cualquier consulta sobre autos, nuestros servicios, tasaciones o cómo usar la web. ¡Te responderé de inmediato!</p>
                        </div>
                    </div>
                    <div class="cq-chatbot-input-area">
                        <form id="cq-chatbot-form" style="display: flex; gap: 8px; width: 100%;">
                            <input type="text" id="cq-chatbot-input" placeholder="Pregúntame lo que quieras..." required autocomplete="off">
                            <button type="submit"><i class="fa-solid fa-paper-plane"></i></button>
                        </form>
                    </div>
                </div>
                <button id="cq-chatbot-trigger">
                    <i class="fa-solid fa-robot"></i>
                </button>
            </div>
        `;
        $('body').append(chatbotHtml);

        // Lógica de interactividad del Chatbot
        const trigger = $('#cq-chatbot-trigger');
        const windowEl = $('#cq-chatbot-window');
        const closeBtn = $('#cq-chatbot-close');
        const form = $('#cq-chatbot-form');
        const input = $('#cq-chatbot-input');
        const messagesContainer = $('#cq-chatbot-messages');

        const history = [];

        trigger.on('click', function () {
            if (windowEl.is(':visible')) {
                windowEl.fadeOut(200);
            } else {
                windowEl.fadeIn(200, function() {
                    input.focus();
                });
                scrollToBottom();
            }
        });

        closeBtn.on('click', function () {
            windowEl.fadeOut(200);
        });

        function scrollToBottom() {
            messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
        }

        function appendMessage(text, role) {
            const formattedText = text
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            
            const bubble = $('<div>')
                .addClass(`cq-msg ${role}`)
                .html(`<p style="margin:0;">${formattedText}</p>`);
            
            messagesContainer.append(bubble);
        }

        function appendTypingIndicator() {
            const bubble = $('<div>')
                .addClass('cq-msg assistant')
                .html('<div class="cq-typing"><span></span><span></span><span></span></div>');
            messagesContainer.append(bubble);
            return bubble;
        }

        form.on('submit', function (e) {
            e.preventDefault();
            const text = input.val().trim();
            if (!text) return;

            input.val('');
            appendMessage(text, 'user');
            history.push({ role: 'user', content: text });
            scrollToBottom();

            const typingIndicator = appendTypingIndicator();
            scrollToBottom();

            $.ajax({
                url: '/api/asesor/chat',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ messages: history }),
                success: function (response) {
                    typingIndicator.remove();
                    if (response.respuesta) {
                        // Limpiar tags de recomendación de autos para el widget flotante chico
                        let cleanedResponse = response.respuesta
                            .replace(/\[CAR_ID:\s*\d+\]/g, '')
                            .replace(/\[EXTERNAL_CAR:[^\]]+\]/g, '');
                        
                        appendMessage(cleanedResponse, 'assistant');
                        history.push({ role: 'assistant', content: response.respuesta });
                    } else {
                        appendMessage('Lo siento, hubo un problema al procesar tu solicitud. Por favor intenta de nuevo.', 'assistant');
                    }
                    scrollToBottom();
                },
                error: function () {
                    typingIndicator.remove();
                    appendMessage('Lo siento, en este momento tengo problemas de conexión. Por favor intenta de nuevo.', 'assistant');
                    scrollToBottom();
                }
            });
        });
    });
})(jQuery);

