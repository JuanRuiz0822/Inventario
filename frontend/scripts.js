
        
        // Global variables
        let allArticulos = [];
        let filteredArticulos = [];
        let currentPage = 1;
        const itemsPerPage =10;

        // Initialize
        // Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadCategorias();
    loadResponsables();
    loadArticulos();

    // ✅ Aquí dentro conectamos el botón una vez que existe en el DOM
    document.getElementById('loadMoreBtn').addEventListener('click', () => {
        currentPage++;
        renderTable();
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
                document.getElementById('valorTotal').textContent = '$' + data.valor_total.toLocaleString('es-CO', {maximumFractionDigits: 0});
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
        async function loadArticulos() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('tableSection').style.display = 'none';
            
            try {
                const response = await fetch('/api/articulos');
                const data = await response.json();
                allArticulos = data.articulos;
                filteredArticulos = [...allArticulos];
                currentPage = 1;
                renderTable();
                showAlert('Datos cargados exitosamente', 'success');
            } catch (error) {
                console.error('Error loading articulos:', error);
                showAlert('Error al cargar los datos', 'error');
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('tableSection').style.display = 'block';
            }
        }

        // Función para refrescar datos al presionar el botón
        async function refreshData() {
             await loadStats();      // Actualiza las estadísticas
             await loadArticulos();  // Carga los artículos y dispara el alert
        } 

        // Conectar el botón de "Actualizar Datos" a la función
        document.getElementById('btnActualizar').addEventListener('click', refreshData);

        // Apply filters
        function applyFilters() {
    // Captura los valores desde los campos de búsqueda/filtro
    const placa = document.getElementById('searchPlaca').value.toLowerCase().trim();
    const consecutivo = document.getElementById('searchConsec').value.toLowerCase().trim();
    const responsable = document.getElementById('filterResponsable').value.toLowerCase().trim();

    filteredArticulos = allArticulos.filter(art => {
        const valorPlaca = (art.placa || '').toLowerCase();
        const valorConsec = (art.consec || '').toLowerCase();
        const valorResponsable = (art.responsable || '').toLowerCase().trim();


        const matchPlaca = !placa || valorPlaca.includes(placa);
        const matchConsec = !consecutivo || valorConsec.includes(consecutivo);
        const matchResponsable = !responsable || valorResponsable === responsable;

        return matchPlaca && matchConsec && matchResponsable;
    });

    currentPage = 1;
    renderTable();
    showAlert(`Se encontraron ${filteredArticulos.length} resultados`, 'success');
}


        // Clear filters
        function clearFilters() {
            document.getElementById('searchPlaca').value = '';
            document.getElementById('searchConsec').value = '';
            document.getElementById('filterResponsable').value = '';
            filteredArticulos = [...allArticulos];
            currentPage = 1;
            renderTable();
        }

        // Render table
        function renderTable() {
    const start = 0; // siempre empezamos desde el primero
    const end = currentPage * itemsPerPage; // mostramos más según la página
    const pageArticulos = filteredArticulos.slice(0, end);

    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    pageArticulos.forEach(art => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge badge-info">${art.placa || art["Placa"] || ''}</span>
<td>${art.nombre || art["Descripción Actual"] || art["Desc."] || ''}</td>
<td>${art.modelo || art["Modelo"] || 'N/A'}</td>
<td>${art.responsable || art["Responsable"] || art["Origen"] || 'Sin responsable'}</td>

                <button class="btn btn-primary btn-sm" onclick="viewDetail('${art.placa ||''}')">
                    👁️ Ver
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Actualizar info de la tabla
    document.getElementById('showingFrom').textContent = 1;
    document.getElementById('showingTo').textContent = Math.min(end, filteredArticulos.length);
    document.getElementById('totalResults').textContent = filteredArticulos.length;

     // Actualizar paginación
    const totalPages = Math.ceil(filteredArticulos.length / itemsPerPage);
    document.getElementById('currentPage').textContent = currentPage;
    document.getElementById('totalPages').textContent = totalPages;

    // Mostrar u ocultar botón "Ver más"
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (end >= filteredArticulos.length) {
        loadMoreBtn.style.display = 'none';
    } else {
        loadMoreBtn.style.display = 'inline-block';
    }
}
     document.getElementById('loadMoreBtn').addEventListener('click', () => {
        currentPage++;
        renderTable();
    });
 
        // Pagination
        function previousPage() {
            if (currentPage > 1) {
                currentPage--;
                renderTable();
                window.scrollTo(0, 0);
            }
        }

        function nextPage() {
            const totalPages = Math.ceil(filteredArticulos.length / itemsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                renderTable();
                window.scrollTo(0, 0);
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
            await loadArticulos();
        }

        // Export data
        function exportData() {
            const csvContent = convertToCSV(filteredArticulos);
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `inventario_${new Date().toISOString().split('T')[0]}.csv`;
            link.click();
            showAlert('Datos exportados exitosamente', 'success');
        }

        function convertToCSV(data) {
            const headers = ['Centro','Placa', 'Modelo', 'Fecha Adquisición','Ubicación','Consec.','Desc.','Descripción Actual',
                'Atributos','Evidencias','Origen'
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
