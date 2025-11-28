// ======================
// VARIABLES GLOBALES
// ======================
let allArticulos = [];
let filteredArticulos = [];
let currentPage = 1;
const itemsPerPage = 10;

// Para reutilizar datos en ver / editar
let articuloActual = null;
let modoEdicion = false;

// ======================
// INICIALIZACIÓN
// ======================
document.addEventListener('DOMContentLoaded', function () {
    loadStats();
    loadCategorias();
    loadResponsables();
    loadArticulosConFiltros(1);

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

// ======================
// ALERTAS
// ======================
function showAlert(message, type = 'success') {
    const alertElement = type === 'success'
        ? document.getElementById('alertSuccess')
        : document.getElementById('alertError');

    alertElement.textContent = message;
    alertElement.style.display = 'block';

    setTimeout(() => {
        alertElement.style.display = 'none';
    }, 5000);
}

// ======================
// ESTADÍSTICAS
// ======================
async function loadStats() {
    try {
        const response = await fetch('/api/inventario/estadisticas');
        const data = await response.json();

        document.getElementById('totalArticulos').textContent =
            data.total_articulos.toLocaleString();
        document.getElementById('totalHojas').textContent =
            data.hojas_procesadas.toLocaleString();
        document.getElementById('totalResponsables').textContent =
            data.responsables_unicos.toLocaleString();
        document.getElementById('valorTotal').textContent =
            '$' + data.valor_total.toLocaleString('es-CO', { maximumFractionDigits: 0 });
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ======================
// CARGAR CATEGORÍAS
// ======================
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

// ======================
// CARGAR RESPONSABLES
// ======================
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

// ======================
// CONSULTA PRINCIPAL
// ======================
async function loadArticulosConFiltros(page = 1) {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('tableSection').style.display = 'none';

    const placa = document.getElementById('searchPlaca').value.trim();
    const consecutivo = document.getElementById('searchConsec').value.trim();
    const responsable = document.getElementById('filterResponsable').value.trim();
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;

    const params = new URLSearchParams({
        page,
        limit: itemsPerPage
    });

    if (placa) params.append('placa', placa);
    if (consecutivo) params.append('consecutivo', consecutivo);
    if (responsable) params.append('responsable', responsable);
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    try {
        const response = await fetch(`/api/inventario/consulta?${params.toString()}`);
        const data = await response.json();

        allArticulos = page === 1 ? data.articulos : allArticulos.concat(data.articulos);
        filteredArticulos = [...allArticulos];

        currentPage = page;
        renderTable();

        showAlert(`Se encontraron ${data.total} resultados`, 'success');

        document.getElementById('currentPage').textContent = currentPage;
        document.getElementById('totalPages').textContent = data.total_pages || 1;

        document.getElementById('loadMoreBtn').style.display =
            currentPage >= data.total_pages ? 'none' : 'inline-block';
    } catch (error) {
        console.error('Error cargando artículos con filtros:', error);
        showAlert('Error al cargar los datos', 'error');
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('tableSection').style.display = 'block';
    }
}

// ======================
// LIMPIAR FILTROS DE FECHA
// ======================
function clearDateFilter() {
    document.getElementById('fechaInicio').value = '';
    document.getElementById('fechaFin').value = '';
    loadArticulosConFiltros(1);
}

// ======================
// CARGAR MÁS ARTÍCULOS
// ======================
async function loadMoreArticulos() {
    const nextPage = currentPage + 1;

    const params = new URLSearchParams({
        page: nextPage,
        limit: itemsPerPage
    });

    const placa = document.getElementById('searchPlaca').value.trim();
    const consecutivo = document.getElementById('searchConsec').value.trim();
    const responsable = document.getElementById('filterResponsable').value.trim();
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;

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

        document.getElementById('loadMoreBtn').style.display =
            currentPage >= data.total_pages ? 'none' : 'inline-block';
    } catch (error) {
        console.error('Error cargando más artículos:', error);
        showAlert('Error al cargar más artículos', 'error');
    }
}

// ======================
// TABLA PRINCIPAL
// ======================
function renderTable() {
    const end = currentPage * itemsPerPage;
    const pageArticulos = filteredArticulos.slice(0, end);

    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    pageArticulos.forEach(art => {
        const placaVal = art.placa || art["Placa"] || '';

        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge badge-info">${placaVal}</span></td>
            <td>${art.nombre || art["Descripción Actual"] || art["Desc."] || ''}</td>
            <td>${art.modelo || art["Modelo"] || 'N/A'}</td>
            <td>${art.responsable || art["Responsable"] || art["Origen"] || 'Sin responsable'}</td>
            <td>
                <div class="crud-actions">
                    <button class="btn btn-success btn-sm" onclick="viewDetail('${placaVal}')">Ver</button>
                    <button class="btn btn-warning btn-sm" onclick="editArticulo('${placaVal}')">Editar</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteArticulo('${placaVal}')">Eliminar</button>
                </div>
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

    document.getElementById('loadMoreBtn').style.display =
        currentPage >= totalPages ? 'none' : 'inline-block';
}

// ======================
// VER DETALLE (modo solo lectura)
// ======================
async function viewDetail(placa) {
    modoEdicion = false;
    try {
        const response = await fetch(`/api/inventario/${placa}/detalle`);
        const data = await response.json();

        if (!data.articulo) return;

        const art = data.articulo;
        articuloActual = art;

        document.getElementById('modalTitle').textContent = '📦 Detalle del Artículo';
        const btnGuardar = document.getElementById('btnGuardarCambios');
        if (btnGuardar) btnGuardar.style.display = 'none';

        document.getElementById('editPlaca').value = art.placa || art["Placa"] || '';
        document.getElementById('editModelo').value = art.modelo || art["Modelo"] || '';
        document.getElementById('editCentro').value = art.Centro || '';
        document.getElementById('editConsec').value = art.consec || art["Consec."] || '';
        document.getElementById('editDesc').value = art["Desc."] || '';
        document.getElementById('editDescripcionActual').value = art["Descripción Actual"] || '';
        document.getElementById('editAtributos').value = art.Atributos || '';
        document.getElementById('editFechaAdq').value = art["Fecha Adquisición"] || art.fecha_adquisicion || '';
        document.getElementById('editUbicacion').value = art.Ubicación || art.ubicacion || '';
        document.getElementById('editEvidencias').value = art.Evidencias || '';
        document.getElementById('editOrigen').value = art.Origen || art.responsable || art["Responsable"] || '';

        document.querySelectorAll('.detail-input').forEach(inp => inp.setAttribute('disabled', 'disabled'));

        document.getElementById('detailModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading detail:', error);
        showAlert('No se pudo cargar el detalle del artículo', 'error');
    }
}

// ======================
// EDITAR ARTÍCULO (modal completo)
// ======================
async function editArticulo(placa) {
    modoEdicion = true;
    try {
        const response = await fetch(`/api/inventario/${placa}/detalle`);
        const data = await response.json();

        if (!data.articulo) return;

        const art = data.articulo;
        articuloActual = art;

        document.getElementById('modalTitle').textContent = '✏️ Editar Artículo';
        const btnGuardar = document.getElementById('btnGuardarCambios');
        if (btnGuardar) btnGuardar.style.display = 'inline-block';

        document.getElementById('editPlaca').value = art.placa || art["Placa"] || '';
        document.getElementById('editModelo').value = art.modelo || art["Modelo"] || '';
        document.getElementById('editCentro').value = art.Centro || '';
        document.getElementById('editConsec').value = art.consec || art["Consec."] || '';
        document.getElementById('editDesc').value = art["Desc."] || '';
        document.getElementById('editDescripcionActual').value = art["Descripción Actual"] || '';
        document.getElementById('editAtributos').value = art.Atributos || '';
        document.getElementById('editFechaAdq').value = art["Fecha Adquisición"] || art.fecha_adquisicion || '';
        document.getElementById('editUbicacion').value = art.Ubicación || art.ubicacion || '';
        document.getElementById('editEvidencias').value = art.Evidencias || '';
        document.getElementById('editOrigen').value = art.Origen || art.responsable || art["Responsable"] || '';

        document.querySelectorAll('.detail-input').forEach(inp => inp.removeAttribute('disabled'));
        document.getElementById('editPlaca').setAttribute('disabled', 'disabled');

        document.getElementById('detailModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading detail for edit:', error);
        showAlert('No se pudo cargar la información para editar', 'error');
    }
}

// ======================
// GUARDAR CAMBIOS (PUT)
// ======================
function guardarCambios() {
    if (!articuloActual) {
        showAlert('No hay artículo cargado', 'error');
        return;
    }
    const placa = articuloActual.placa || articuloActual["Placa"];
    if (!placa) {
        showAlert('Placa no válida', 'error');
        return;
    }

    const payload = {
        "Centro": document.getElementById('editCentro').value,
        "Modelo": document.getElementById('editModelo').value,
        "Consec.": document.getElementById('editConsec').value,
        "Desc.": document.getElementById('editDesc').value,
        "Descripción Actual": document.getElementById('editDescripcionActual').value,
        "Placa": placa,
        "Atributos": document.getElementById('editAtributos').value,
        "Fecha Adquisición": document.getElementById('editFechaAdq').value,
        "Ubicación": document.getElementById('editUbicacion').value,
        "Evidencias": document.getElementById('editEvidencias').value,
        "Origen": document.getElementById('editOrigen').value
    };

    fetch(`/api/inventario/${placa}/editar`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then(resp => {
            if (!resp.ok) throw new Error('Error en edición');
            return resp.json();
        })
        .then(() => {
            showAlert('Artículo editado correctamente', 'success');
            document.getElementById('detailModal').style.display = 'none';
            articuloActual = null;
            loadArticulosConFiltros(currentPage);
        })
        .catch(() => {
            showAlert('Error al editar el artículo', 'error');
        });
}

// ======================
// ELIMINAR ARTÍCULO
// ======================
function deleteArticulo(placa) {
    if (!confirm(`¿Seguro que deseas eliminar la placa ${placa}?`)) {
        return;
    }

    fetch(`/api/inventario/${placa}/eliminar`, {
        method: 'DELETE'
    })
        .then(resp => {
            if (!resp.ok) throw new Error('Error en eliminado');
            return resp.json();
        })
        .then(() => {
            showAlert('Artículo eliminado correctamente', 'success');
            loadArticulosConFiltros(1);
        })
        .catch(() => showAlert('Error al eliminar el artículo', 'error'));
}

// ======================
// MODAL
// ======================
function closeModal() {
    document.getElementById('detailModal').style.display = 'none';
    articuloActual = null;
    modoEdicion = false;
}

window.onclick = function (event) {
    const modal = document.getElementById('detailModal');
    if (event.target === modal) closeModal();
};

// ======================
// REFRESCAR DATOS
// ======================
async function refreshData() {
    await loadStats();
    await loadArticulosConFiltros(1);
}

// ======================
// EXPORTAR CSV
// ======================
function exportData() {
    const placa = document.getElementById('searchPlaca').value.trim();
    const consecutivo = document.getElementById('searchConsec').value.trim();
    const responsable = document.getElementById('filterResponsable').value.trim();
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;

    const params = new URLSearchParams({
        exportar_todo: 'true'
    });

    if (placa) params.append('placa', placa);
    if (consecutivo) params.append('consecutivo', consecutivo);
    if (responsable) params.append('responsable', responsable);
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    fetch(`/api/inventario/consulta?${params.toString()}`)
        .then(resp => resp.json())
        .then(data => {
            const csvContent = convertToCSV(data.articulos);

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');

            link.href = URL.createObjectURL(blob);
            link.download = `inventario_${new Date().toISOString().split('T')[0]}.csv`;
            link.click();

            showAlert(`Datos exportados exitosamente (${data.articulos.length} registros)`, 'success');
        })
        .catch(() => {
            showAlert('Error al exportar los datos', 'error');
        });
}

// ======================
// CONVERTIR A CSV
// ======================
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

    let csv = headers.join(',') + '\n';

    rows.forEach(row => {
        csv += row.map(col => `"${String(col).replace(/"/g, '""')}"`).join(',') + '\n';
    });

    return csv;
}
