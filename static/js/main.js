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
                    position: fixed !important;
                    bottom: 165px !important;
                    right: 30px !important;
                    z-index: 9999 !important;
                    font-family: 'Rubik', sans-serif !important;
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
                #cq-chatbot-window, #cq-chatbot-window * {
                    box-sizing: border-box !important;
                }
                #cq-chatbot-window {
                    position: fixed !important;
                    bottom: 235px !important;
                    right: 30px !important;
                    width: 350px !important;
                    min-width: 350px !important;
                    max-width: calc(100vw - 60px) !important;
                    height: 460px !important;
                    background-color: #0b0f19 !important;
                    border: 1px solid rgba(255, 255, 255, 0.1) !important;
                    border-radius: 15px !important;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                    transition: all 0.3s ease;
                    z-index: 10000 !important;
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
                #cq-whatsapp-float {
                    position: fixed !important;
                    bottom: 95px !important;
                    right: 30px !important;
                    width: 58px !important;
                    height: 58px !important;
                    border-radius: 50% !important;
                    background-color: #25D366 !important;
                    color: #ffffff !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important;
                    z-index: 9999 !important;
                    text-decoration: none !important;
                    transition: all 0.3s ease !important;
                }
                #cq-whatsapp-float:hover {
                    transform: scale(1.08) !important;
                    box-shadow: 0 6px 20px rgba(37, 211, 102, 0.6) !important;
                    background-color: #20ba5a !important;
                }
            `)
            .appendTo('head');

        // Inyectar la estructura HTML del Chatbot y WhatsApp Flotante
        const chatbotHtml = `
            <div id="cq-chatbot-container">
                <div id="cq-chatbot-window">
                    <div class="cq-chatbot-header">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="cq-chatbot-avatar" style="background: #ffffff; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; padding: 3px; border: 2px solid #fbd333;">
                                <img src="/static/img/CarroQhatuL.png" alt="CarroQhatu" style="width: 100%; height: 100%; object-fit: contain;">
                            </div>
                            <div>
                                <h6 style="margin: 0; color: #fff; font-weight: 700; font-size: 0.95rem;">Qhatuchay IA 🚗🤖</h6>
                                <small style="color: #fbd333; font-size: 0.75rem; display: flex; align-items: center; gap: 4px; font-weight: 600;">
                                    <span class="cq-pulse-dot"></span> Asesor Oficial CarroQhatu
                                </small>
                            </div>
                        </div>
                        <button id="cq-chatbot-close" style="background: none; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer;">&times;</button>
                    </div>
                    <div id="cq-chatbot-messages">
                        <div class="cq-msg assistant">
                            <p style="margin:0;">¡Hola! Soy <strong>Qhatuchay IA</strong> 🚗🤖, el asesor oficial de <strong>CarroQhatu</strong>.<br><br>Te doy TODA la información de nuestra página web: vehículos del catálogo, precios, contacto directo por WhatsApp (+51 972043502), Inspección 360°, cotizaciones o cómo comprar/vender tu auto. ¡Pregúntame cualquier cosa de nuestra web!</p>
                        </div>
                    </div>
                    <div class="cq-chatbot-input-area">
                        <form id="cq-chatbot-form" style="display: flex; gap: 8px; width: 100%;">
                            <input type="text" id="cq-chatbot-input" placeholder="Pregúntale a Qhatuchay IA sobre la web..." required autocomplete="off">
                            <button type="submit" title="Enviar"><i class="fa-solid fa-paper-plane"></i></button>
                        </form>
                    </div>
                </div>
                <button id="cq-chatbot-trigger" title="Qhatuchay IA - Asesor CarroQhatu" style="padding: 0; background-color: #fbd333; border: 2px solid #000; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                    <img src="/static/img/CarroQhatuL.png" alt="Qhatuchay IA" style="width: 44px; height: 44px; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
                </button>
            </div>

            <!-- Botón flotante directo de WhatsApp debajo del Chatbot -->
            <a id="cq-whatsapp-float" href="https://wa.me/51972043502?text=Hola%20CarroQhatu!%20Deseo%20informaci%C3%B3n%20y%20asesor%C3%ADa%20personalizada." target="_blank" title="Contactar por WhatsApp (+51 972043502)">
                <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" alt="WhatsApp" style="width: 34px; height: 34px; object-fit: contain;">
            </a>
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
                windowEl.css('display', 'flex').hide().fadeIn(200, function() {
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

