// Global variables
let allArticulos = [];
let filteredArticulos = [];
let currentPage = 1;
const itemsPerPage = 10;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadCategorias();
    loadResponsables();
    loadArticulosConFiltros(1);

    // Conectar botones usando IDs únicos:
    document.getElementById('btnBuscar').addEventListener('click', () => {
        loadArticulosConFiltros(1);
    });

    document.getElementById('btnLimpiarFiltros').addEventListener('click', () => {
        document.getElementById('searchPlaca').value = '';
        document.getElementById('searchConsec').value = '';
        document.getElementById('filterResponsable').value = '';
        document.getElementById('fechaInicio').value = '';
        document.getElementById('fechaFin').value = '';
        loadArticulosConFiltros(1);
    });

    document.getElementById('btnExportar').addEventListener('click', exportData);

    document.getElementById('btnBuscarFechas').addEventListener('click', () => {
        loadArticulosConFiltros(1);
    });

    document.getElementById('btnLimpiarFechas').addEventListener('click', clearDateFilter);

    document.getElementById('loadMoreBtn').addEventListener('click', () => {
        loadMoreArticulos();
    });
});

// Show alert
function showAlert(message, type = 'success') {
    const alertElement = type === 'success' ? document.getElementById('alertSuccess') : document.getElementById('alertError');
    alertElement.textContent = message;
    alertElement.style.display = 'block';
    setTimeout(() => {
        alertElement.style.display = 'none';
    }, 5000);
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/inventario/estadisticas');
        const data = await response.json();
        document.getElementById('totalArticulos').textContent = data.total_articulos.toLocaleString();
        document.getElementById('totalHojas').textContent = data.hojas_procesadas.toLocaleString();
        document.getElementById('totalResponsables').textContent = data.responsables_unicos.toLocaleString();
        document.getElementById('valorTotal').textContent = '$' + data.valor_total.toLocaleString('es-CO', { maximumFractionDigits: 0 });
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load categorias
async function loadCategorias() {
    try {
        const response = await fetch('/api/inventario/categorias');
        const categorias = await response.json();
        const select = document.getElementById('filterCategoria');
        categorias.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading categorias:', error);
    }
}

// Load responsables
async function loadResponsables() {
    try {
        const response = await fetch('/api/inventario/responsables');
        const responsables = await response.json();
        const select = document.getElementById('filterResponsable');
        responsables.forEach(resp => {
            const option = document.createElement('option');
            option.value = resp;
            option.textContent = resp;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading responsables:', error);
    }
}

// Load articulos
async function loadArticulosConFiltros(page = 1) {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('tableSection').style.display = 'none';

    const placa = document.getElementById('searchPlaca').value.trim();
    const consecutivo = document.getElementById('searchConsec').value.trim();
    const responsable = document.getElementById('filterResponsable').value.trim();
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;

    const params = new URLSearchParams();
    params.append('page', page);
    params.append('limit', itemsPerPage);

    if (placa) params.append('placa', placa);
    if (consecutivo) params.append('consecutivo', consecutivo);
    if (responsable) params.append('responsable', responsable);
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    try {
        const response = await fetch(`/api/inventario/consulta?${params.toString()}`);
        const data = await response.json();

        if (page === 1) {
            allArticulos = data.articulos;
        } else {
            allArticulos = allArticulos.concat(data.articulos);
        }

        filteredArticulos = [...allArticulos];
        currentPage = page;
        renderTable();

        showAlert(`Se encontraron ${data.total} resultados`, 'success');
        document.getElementById('currentPage').textContent = currentPage;
        document.getElementById('totalPages').textContent = data.total_pages || 1;

        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (currentPage >= data.total_pages) {
            loadMoreBtn.style.display = 'none';
        } else {
            loadMoreBtn.style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Error cargando artículos con filtros:', error);
        showAlert('Error al cargar los datos', 'error');
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('tableSection').style.display = 'block';
    }
}

function clearDateFilter() {
    document.getElementById('fechaInicio').value = '';
    document.getElementById('fechaFin').value = '';
    loadArticulosConFiltros(1);
}

// Botón "Ver más" paginación
async function loadMoreArticulos() {
    const nextPage = currentPage + 1;
    const placa = document.getElementById('searchPlaca').value.trim();
    const consecutivo = document.getElementById('searchConsec').value.trim();
    const responsable = document.getElementById('filterResponsable').value.trim();
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;

    const params = new URLSearchParams();
    params.append('page', nextPage);
    params.append('limit', itemsPerPage);
    if (placa) params.append('placa', placa);
    if (consecutivo) params.append('consecutivo', consecutivo);
    if (responsable) params.append('responsable', responsable);
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    try {
        const response = await fetch(`/api/inventario/consulta?${params.toString()}`);
        const data = await response.json();

        allArticulos = allArticulos.concat(data.articulos);
        filteredArticulos = [...allArticulos];
        currentPage = nextPage;
        renderTable();

        if (currentPage >= data.total_pages) {
            document.getElementById('loadMoreBtn').style.display = 'none';
        } else {
            document.getElementById('loadMoreBtn').style.display = 'inline-block';
        }

    } catch (error) {
        console.error('Error cargando más artículos:', error);
        showAlert('Error al cargar más artículos', 'error');
    }
}

// Render table
function renderTable() {
    const end = currentPage * itemsPerPage;
    const pageArticulos = filteredArticulos.slice(0, end);

    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    pageArticulos.forEach(art => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge badge-info">${art.placa || art["Placa"] || ''}</span></td>
            <td>${art.nombre || art["Descripción Actual"] || art["Desc."] || ''}</td>
            <td>${art.modelo || art["Modelo"] || 'N/A'}</td>
            <td>${art.responsable || art["Responsable"] || art["Origen"] || 'Sin responsable'}</td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="viewDetail('${art.placa || ''}')">
                    👁️ Ver
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    document.getElementById('showingFrom').textContent = 1;
    document.getElementById('showingTo').textContent = Math.min(end, filteredArticulos.length);
    document.getElementById('totalResults').textContent = filteredArticulos.length;

    const totalPages = Math.ceil(filteredArticulos.length / itemsPerPage);
    document.getElementById('currentPage').textContent = currentPage;
    document.getElementById('totalPages').textContent = totalPages;

    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (currentPage >= totalPages) {
        loadMoreBtn.style.display = 'none';
    } else {
        loadMoreBtn.style.display = 'inline-block';
    }
}

// View detail
async function viewDetail(placa) {
    try {
        const response = await fetch(`/api/inventario/${placa}/detalle`);
        const data = await response.json();

        if (data.articulo) {
            const art = data.articulo;
            const modalBody = document.getElementById('modalBody');
            modalBody.innerHTML = `
                <div class="detail-grid">
                    <div class="detail-item"><div class="detail-label">Placa</div><div class="detail-value">${art.placa || art["Placa"] || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Modelo</div><div class="detail-value">${art.modelo || art["Modelo"] || 'N/A'}</div></div>
                    <div class="detail-item"><div class="detail-label">Centro</div><div class="detail-value">${art.Centro || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Consec.</div><div class="detail-value">${art.consec || art["Consec."] || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Desc.</div><div class="detail-value">${art["Desc."] || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Descripción Actual</div><div class="detail-value">${art["Descripción Actual"] || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Atributos</div><div class="detail-value">${art.Atributos || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Fecha Adquisición</div><div class="detail-value">${art["Fecha Adquisición"] || art.fecha_adquisicion || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Ubicación</div><div class="detail-value">${art.Ubicación || art.ubicacion || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Evidencias</div><div class="detail-value">${art.Evidencias || ''}</div></div>
                    <div class="detail-item"><div class="detail-label">Origen</div><div class="detail-value">${art.Origen || art.responsable || art["Responsable"] || ''}</div></div>
                </div>
            `;
            document.getElementById('detailModal').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading detail:', error);
        showAlert('No se pudo cargar el detalle del artículo', 'error');
    }
}

// Close modal
function closeModal() {
    document.getElementById('detailModal').style.display = 'none';
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('detailModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Refresh data
async function refreshData() {
    await loadStats();
    await loadArticulosConFiltros(1);
}

// Export data
function exportData() {
    // Toma los filtros activos (como lo hace loadArticulosConFiltros)
    const placa = document.getElementById('searchPlaca').value.trim();
    const consecutivo = document.getElementById('searchConsec').value.trim();
    const responsable = document.getElementById('filterResponsable').value.trim();
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;

    const params = new URLSearchParams();
    if (placa) params.append('placa', placa);
    if (consecutivo) params.append('consecutivo', consecutivo);
    if (responsable) params.append('responsable', responsable);
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);
    params.append('exportar_todo', 'true'); // <-- Clave para pedir todos los registros al backend

    fetch(`/api/inventario/consulta?${params.toString()}`)
        .then(resp => resp.json())
        .then(data => {
            const csvContent = convertToCSV(data.articulos);
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `inventario_${new Date().toISOString().split('T')[0]}.csv`;
            link.click();
            showAlert('Datos exportados exitosamente', 'success');
        })
        .catch(error => {
            showAlert('Error al exportar los datos', 'error');
        });
}


function convertToCSV(data) {
    const headers = [
        'Centro', 'Placa', 'Modelo', 'Fecha Adquisición', 'Ubicación', 'Consec.',
        'Desc.', 'Descripción Actual', 'Atributos', 'Evidencias', 'Origen'
    ];
    const rows = data.map(art => [
        art["Centro"] || '',
        art["Placa"] || '',
        art["Modelo"] || '',
        art["Fecha Adquisición"] || '',
        art["Ubicación"] || '',
        art["Consec."] || '',
        art["Desc."] || '',
        art["Descripción Actual"] || '',
        art["Atributos"] || '',
        art["Evidencias"] || '',
        art["Origen"] || ''
    ]);
    const BOM = '\uFEFF';
    return BOM + [headers, ...rows].map(
        row => row.map(cell => `"${cell}"`).join(';')
    ).join('\n');
}

/* cambios 1.12 */
