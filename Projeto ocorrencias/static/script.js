// Sistema de Ocorrências - SIO
console.log('🔧 SIO - Sistema carregado');

// Estado global
let estado = {
    ocorrencias: [],
    filtroCategoria: '',
    carregando: false
};

// Quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Página carregada');
    
    // Inicializa funcionalidades baseadas na página
    inicializarPagina();
});

function inicializarPagina() {
    // Página de consulta
    if (document.getElementById('listaOcorrencias')) {
        console.log('🔄 Iniciando carga de ocorrências...');
        carregarOcorrencias();
        
        // Inicializa filtros
        const filtroCategoria = document.getElementById('filtroCategoria');
        if (filtroCategoria) {
            filtroCategoria.addEventListener('change', aplicarFiltros);
        }
    }
    
    // Página de registro
    if (document.getElementById('formOcorrencia')) {
        inicializarFormulario();
    }
    
    // Animações de entrada
    animarEntrada();
}

function animarEntrada() {
    const elementos = document.querySelectorAll('.fade-in');
    elementos.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// ========== FORMULÁRIO MELHORADO ==========
function inicializarFormulario() {
    const form = document.getElementById('formOcorrencia');
    const contadorDescricao = document.getElementById('contadorDescricao');
    const textareaDescricao = form.querySelector('textarea[name="descricao"]');
    
    // Contador de caracteres para descrição
    if (textareaDescricao && contadorDescricao) {
        textareaDescricao.addEventListener('input', function() {
            const length = this.value.length;
            contadorDescricao.textContent = `${length}/500 caracteres`;
            
            if (length > 450) {
                contadorDescricao.className = 'text-sm text-orange-500';
            } else {
                contadorDescricao.className = 'text-sm text-gray-500';
            }
        });
    }
    
    // Preview de arquivo
    const inputArquivo = form.querySelector('input[name="anexo"]');
    const previewArquivo = document.getElementById('previewArquivo');
    
    if (inputArquivo && previewArquivo) {
        inputArquivo.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                previewArquivo.innerHTML = `
                    <div class="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                        <div class="text-blue-600">
                            ${obterIconeArquivo(file.name)}
                        </div>
                        <div class="flex-1">
                            <p class="font-medium text-sm text-blue-900">${file.name}</p>
                            <p class="text-xs text-blue-600">${formatarTamanhoArquivo(file.size)}</p>
                        </div>
                        <button type="button" onclick="removerArquivo()" class="text-red-500 hover:text-red-700">
                            ✕
                        </button>
                    </div>
                `;
            }
        });
    }
    
    // Submissão do formulário
    form.addEventListener('submit', enviarOcorrencia);
}

function obterIconeArquivo(nomeArquivo) {
    const extensao = nomeArquivo.split('.').pop().toLowerCase();
    const icones = {
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️'
    };
    return icones[extensao] || '📎';
}

function formatarTamanhoArquivo(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function removerArquivo() {
    const inputArquivo = document.querySelector('input[name="anexo"]');
    const previewArquivo = document.getElementById('previewArquivo');
    
    inputArquivo.value = '';
    previewArquivo.innerHTML = '';
}

async function enviarOcorrencia(e) {
    e.preventDefault();
    console.log('📤 Enviando ocorrência...');

    const form = e.target;
    const botao = form.querySelector('button[type="submit"]');

    // Validação adicional
    const titulo = form.querySelector('input[name="titulo"]').value.trim();
    const descricao = form.querySelector('textarea[name="descricao"]').value.trim();
    
    if (titulo.length < 5) {
        mostrarToast('❌ O título deve ter pelo menos 5 caracteres', 'error');
        return;
    }
    
    if (descricao.length < 10) {
        mostrarToast('❌ A descrição deve ter pelo menos 10 caracteres', 'error');
        return;
    }

    // Animação de loading
    botao.disabled = true;
    botao.innerHTML = `
        <div class="flex items-center justify-center space-x-2">
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>Enviando...</span>
        </div>
    `;

    try {
        const formData = new FormData(form);
        
        console.log('📝 Dados do formulário:');
        for (let [key, value] of formData.entries()) {
            if (key !== 'anexo') console.log(`  ${key}: ${value}`);
        }

        const resposta = await fetch('/api/registrar', {
            method: 'POST',
            body: formData
        });

        console.log(`📨 Status: ${resposta.status}`);
        const resultado = await resposta.json();

        if (resposta.ok) {
            mostrarToast('✅ ' + resultado.mensagem, 'success');
            form.reset();
            removerArquivo();
            
            // Redireciona após sucesso
            setTimeout(() => {
                window.location.href = '/consultar';
            }, 2000);
            
        } else {
            mostrarToast('❌ ' + (resultado.erro || 'Erro desconhecido'), 'error');
        }

    } catch (erro) {
        console.error('❌ Erro de rede:', erro);
        mostrarToast('❌ Erro de conexão com o servidor', 'error');
    } finally {
        // Restaura botão
        botao.disabled = false;
        botao.textContent = 'Enviar Ocorrência';
    }
}

// ========== CONSULTA MELHORADA ==========
async function carregarOcorrencias() {
    console.log('📋 Buscando ocorrências...');
    
    const lista = document.getElementById('listaOcorrencias');
    const semOcorrencias = document.getElementById('semOcorrencias');
    const loading = document.getElementById('loadingOcorrencias');

    if (!lista) return;

    // Mostra loading
    estado.carregando = true;
    if (loading) loading.classList.remove('hidden');
    if (lista) lista.classList.add('opacity-50');

    try {
        const resposta = await fetch('/api/ocorrencias');
        console.log(`📨 Status da API: ${resposta.status}`);
        
        if (!resposta.ok) throw new Error(`Erro HTTP: ${resposta.status}`);
        
        const ocorrencias = await resposta.json();
        estado.ocorrencias = ocorrencias;
        
        console.log(`✅ Recebidas ${ocorrencias.length} ocorrências:`, ocorrencias);
        renderizarOcorrencias(ocorrencias);

    } catch (erro) {
        console.error('❌ Erro ao carregar ocorrências:', erro);
        mostrarErroCarregamento(erro);
    } finally {
        estado.carregando = false;
        if (loading) loading.classList.add('hidden');
        if (lista) lista.classList.remove('opacity-50');
    }
}

function renderizarOcorrencias(ocorrencias) {
    const lista = document.getElementById('listaOcorrencias');
    const semOcorrencias = document.getElementById('semOcorrencias');
    const estatisticas = document.getElementById('estatisticas');

    // Limpa lista
    lista.innerHTML = '';

    if (ocorrencias.length === 0) {
        console.log('📭 Nenhuma ocorrência encontrada');
        if (semOcorrencias) semOcorrencias.classList.remove('hidden');
        if (estatisticas) estatisticas.classList.add('hidden');
        return;
    }

    // Esconde mensagem "sem ocorrências"
    if (semOcorrencias) semOcorrencias.classList.add('hidden');
    if (estatisticas) estatisticas.classList.remove('hidden');

    // Atualiza estatísticas
    atualizarEstatisticas(ocorrencias);

    // Adiciona cada ocorrência
    ocorrencias.forEach((ocorrencia, index) => {
        const card = criarCardOcorrencia(ocorrencia);
        lista.appendChild(card);
        
        // Anima a entrada
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    console.log('🎉 Ocorrências exibidas com sucesso!');
}

function criarCardOcorrencia(ocorrencia) {
    const card = document.createElement('div');
    card.className = 'card-hover bg-white rounded-xl border border-gray-200 p-6 mb-4';
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'all 0.6s ease';
    
    const badgeClass = obterClasseBadge(ocorrencia.categoria);
    const statusClass = obterClasseStatus(ocorrencia.status);
    
    card.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 mb-4">
            <div class="flex-1">
                <div class="flex flex-wrap items-center gap-2 mb-2">
                    <h3 class="text-xl font-bold text-gray-900">${ocorrencia.titulo || 'Sem título'}</h3>
                    <span class="${statusClass} px-3 py-1 rounded-full text-sm font-semibold">
                        ${ocorrencia.status || 'Pendente'}
                    </span>
                </div>
                <p class="text-gray-600 leading-relaxed">${ocorrencia.descricao || 'Sem descrição'}</p>
            </div>
            <div class="flex flex-wrap gap-2">
                <span class="${badgeClass} px-3 py-1 rounded-full text-sm font-semibold">
                    ${ocorrencia.categoria || 'Geral'}
                </span>
            </div>
        </div>
        
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pt-4 border-t border-gray-100">
            <div class="flex items-center space-x-4 text-sm text-gray-500">
                <span class="flex items-center space-x-1">
                    <span>📅</span>
                    <span>${ocorrencia.data || 'Data não informada'}</span>
                </span>
                ${ocorrencia.id ? `
                <span class="flex items-center space-x-1">
                    <span>🆔</span>
                    <span>#${ocorrencia.id}</span>
                </span>
                ` : ''}
            </div>
            
            <div class="flex items-center space-x-3">
                <button onclick="verDetalhesOcorrencia(${ocorrencia.id})" 
                        class="flex items-center space-x-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors">
                    <span>👁️</span>
                    <span>Ver Detalhes</span>
                </button>
                
                ${ocorrencia.anexo ? `
                    <a href="${ocorrencia.anexo}" target="_blank" 
                       class="flex items-center space-x-2 bg-green-50 hover:bg-green-100 text-green-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors">
                        <span>📎</span>
                        <span>Ver Anexo</span>
                    </a>
                ` : `
                    <span class="flex items-center space-x-2 bg-gray-50 text-gray-400 px-3 py-2 rounded-lg text-sm">
                        <span>📄</span>
                        <span>Sem anexo</span>
                    </span>
                `}
                
                <button onclick="copiarOcorrencia(${ocorrencia.id})" 
                        class="flex items-center space-x-2 bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                        title="Copiar dados da ocorrência">
                    <span>📋</span>
                    <span>Copiar</span>
                </button>
            </div>
        </div>
    `;
    
    return card;
}

function obterClasseBadge(categoria) {
    const classes = {
        'Infraestrutura': 'badge-infra',
        'Equipamento': 'badge-equip',
        'Segurança': 'badge-seguranca',
        'Limpeza': 'badge-limpeza',
        'Outros': 'badge-outros'
    };
    return classes[categoria] || 'badge-outros';
}

function obterClasseStatus(status) {
    const classes = {
        'Pendente': 'status-pendente',
        'Em Andamento': 'status-andamento',
        'Resolvido': 'status-resolvido'
    };
    return classes[status] || 'status-pendente';
}

function atualizarEstatisticas(ocorrencias) {
    const totalElement = document.getElementById('totalOcorrencias');
    const categoriasElement = document.getElementById('categoriasOcorrencias');
    
    if (totalElement) {
        totalElement.textContent = ocorrencias.length;
    }
    
    if (categoriasElement) {
        const categorias = ocorrencias.reduce((acc, occ) => {
            acc[occ.categoria] = (acc[occ.categoria] || 0) + 1;
            return acc;
        }, {});
        
        categoriasElement.innerHTML = Object.entries(categorias)
            .map(([cat, count]) => `<span class="bg-white bg-opacity-20 px-2 py-1 rounded text-sm mx-1">${cat}: ${count}</span>`)
            .join(' ');
    }
}

function aplicarFiltros() {
    const filtroCategoria = document.getElementById('filtroCategoria');
    const categoria = filtroCategoria ? filtroCategoria.value : '';
    
    let ocorrenciasFiltradas = estado.ocorrencias;
    
    if (categoria) {
        ocorrenciasFiltradas = estado.ocorrencias.filter(occ => 
            occ.categoria === categoria
        );
    }
    
    renderizarOcorrencias(ocorrenciasFiltradas);
}

function limparFiltros() {
    const filtroCategoria = document.getElementById('filtroCategoria');
    if (filtroCategoria) filtroCategoria.value = '';
    
    renderizarOcorrencias(estado.ocorrencias);
}

function copiarOcorrencia(id) {
    const ocorrencia = estado.ocorrencias.find(occ => occ.id === id);
    if (ocorrencia) {
        const texto = `Ocorrência #${ocorrencia.id}\nTítulo: ${ocorrencia.titulo}\nCategoria: ${ocorrencia.categoria}\nDescrição: ${ocorrencia.descricao}\nData: ${ocorrencia.data}\nStatus: ${ocorrencia.status}`;
        navigator.clipboard.writeText(texto).then(() => {
            mostrarToast('📋 Ocorrência copiada para a área de transferência!', 'success');
        });
    }
}

// ========== SISTEMA DE DETALHES ==========
async function verDetalhesOcorrencia(ocorrenciaId) {
    try {
        const loading = document.getElementById('loadingOcorrencias');
        if (loading) loading.classList.remove('hidden');
        
        const response = await fetch(`/api/ocorrencia/${ocorrenciaId}`);
        const data = await response.json();

        if (loading) loading.classList.add('hidden');
        
        if (response.ok) {
            abrirModalDetalhes(data);
        } else {
            mostrarToast(`❌ ${data.erro}`, 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarToast('❌ Erro ao carregar detalhes', 'error');
    }
}

function abrirModalDetalhes(dados) {
    const { ocorrencia, respostas } = dados;
    
    let respostasHTML = '';
    if (respostas && respostas.length > 0) {
        respostasHTML = `
            <div class="mt-6">
                <h4 class="font-semibold text-gray-800 mb-3">💬 Respostas da Administração (${respostas.length})</h4>
                ${respostas.map(resposta => `
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-3">
                        <div class="flex justify-between items-start mb-2">
                            <p class="font-semibold text-blue-800">${resposta.admin_nome || 'Administrador'}</p>
                            <p class="text-sm text-blue-600">${resposta.data_resposta_formatada}</p>
                        </div>
                        <p class="text-blue-700">${resposta.mensagem}</p>
                        ${resposta.anexo ? `
                            <div class="mt-2">
                                <a href="${resposta.anexo}" target="_blank" class="inline-flex items-center space-x-2 text-blue-600 hover:text-blue-800">
                                    <span>📎</span>
                                    <span class="text-sm">Anexo da resposta</span>
                                </a>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        respostasHTML = `
            <div class="mt-6 text-center py-8 bg-gray-50 rounded-lg">
                <div class="text-4xl mb-3">⏳</div>
                <h4 class="font-semibold text-gray-700 mb-2">Aguardando resposta</h4>
                <p class="text-gray-500">Sua ocorrência ainda não foi respondida pela administração.</p>
            </div>
        `;
    }

    const badgeClass = obterClasseBadge(ocorrencia.categoria);
    const statusClass = obterClasseStatus(ocorrencia.status);

    document.getElementById('conteudoDetalhes').innerHTML = `
        <div class="space-y-4">
            <div class="bg-gray-50 p-4 rounded-lg">
                <h4 class="font-semibold text-gray-800 mb-3">📋 Informações da Ocorrência</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <p><strong>ID:</strong> #${ocorrencia.id}</p>
                    <p><strong>Status:</strong> <span class="${statusClass} px-2 py-1 rounded text-sm">${ocorrencia.status}</span></p>
                    <p><strong>Título:</strong> ${ocorrencia.titulo}</p>
                    <p><strong>Categoria:</strong> <span class="${badgeClass} px-2 py-1 rounded text-sm">${ocorrencia.categoria}</span></p>
                    <p><strong>Data:</strong> ${ocorrencia.data_formatada}</p>
                    ${ocorrencia.anexo ? `<p><strong>Anexo:</strong> <a href="${ocorrencia.anexo}" target="_blank" class="text-blue-600 hover:underline">Ver arquivo</a></p>` : ''}
                </div>
            </div>
            
            <div class="bg-gray-50 p-4 rounded-lg">
                <h4 class="font-semibold text-gray-800 mb-2">📝 Descrição</h4>
                <p class="text-gray-700">${ocorrencia.descricao}</p>
            </div>
            
            ${respostasHTML}
        </div>
    `;
    
    document.getElementById('modalDetalhes').classList.remove('hidden');
}

function fecharModalDetalhes() {
    document.getElementById('modalDetalhes').classList.add('hidden');
}

// Fecha modal ao clicar fora
document.getElementById('modalDetalhes')?.addEventListener('click', function(e) {
    if (e.target === this) {
        fecharModalDetalhes();
    }
});

function mostrarErroCarregamento(erro) {
    const lista = document.getElementById('listaOcorrencias');
    const semOcorrencias = document.getElementById('semOcorrencias');
    
    lista.innerHTML = `
        <div class="text-center p-8 bg-red-50 border border-red-200 rounded-xl">
            <div class="text-red-600 text-4xl mb-3">⚠️</div>
            <h3 class="font-semibold text-red-800 text-lg mb-2">Erro ao carregar ocorrências</h3>
            <p class="text-red-600 mb-4">${erro.message}</p>
            <button onclick="carregarOcorrencias()" 
                    class="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors">
                🔄 Tentar Novamente
            </button>
        </div>
    `;
    
    if (semOcorrencias) semOcorrencias.classList.add('hidden');
}

// ========== NOTIFICAÇÕES TOAST ==========
function mostrarToast(mensagem, tipo = 'success') {
    // Remove toast anterior se existir
    const toastAnterior = document.querySelector('.toast');
    if (toastAnterior) toastAnterior.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;
    toast.textContent = mensagem;
    
    document.body.appendChild(toast);
    
    // Remove automaticamente após 5 segundos
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// ========== ATUALIZAÇÃO AUTOMÁTICA ==========
if (document.getElementById('listaOcorrencias')) {
    // Atualiza a cada 30 segundos
    setInterval(() => {
        if (!estado.carregando) {
            console.log('🔄 Atualização automática...');
            carregarOcorrencias();
        }
    }, 30000);
}

// Função global para recarregar
function recarregarOcorrencias() {
    console.log('🔄 Recarregando manualmente...');
    carregarOcorrencias();
}

// ========== UTILITÁRIOS GLOBAIS ==========
function formatarData(data) {
    if (!data) return 'Data não informada';
    return new Date(data).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Exportar funções para uso global
window.recarregarOcorrencias = recarregarOcorrencias;
window.aplicarFiltros = aplicarFiltros;
window.limparFiltros = limparFiltros;
window.copiarOcorrencia = copiarOcorrencia;
window.mostrarToast = mostrarToast;
window.verDetalhesOcorrencia = verDetalhesOcorrencia;
window.fecharModalDetalhes = fecharModalDetalhes;