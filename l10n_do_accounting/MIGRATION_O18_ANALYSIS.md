# Análisis de Migración - l10n_do_accounting a Odoo 18.0

## Resumen Ejecutivo

Este documento detalla los hallazgos del análisis comparativo entre `l10n_do_accounting` y los módulos nativos de localización LATAM (`l10n_ar`, `l10n_cl`) en Odoo 18.0.

---

## 🔍 Módulos Nativos Estudiados

Los siguientes módulos nativos de Odoo 18 fueron analizados como referencia:

| Módulo | País | Ruta |
|--------|------|------|
| `l10n_ar` | Argentina | `/odoo/addons/l10n_ar/models/account_move.py` |
| `l10n_cl` | Chile | `/odoo/addons/l10n_cl/models/account_move.py` |
| `l10n_latam_invoice_document` | Base LATAM | `/odoo/addons/l10n_latam_invoice_document/models/account_move.py` |

---

## 🔴 Diferencias Críticas Identificadas

### 1. Manejo de Secuencias

#### **l10n_ar / l10n_cl (Patrón Nativo)**
```python
class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_starting_sequence(self):
        if self.journal_id.l10n_latam_use_documents and self.country_code == "XX":
            return self._get_formatted_sequence()
        return super()._get_starting_sequence()

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super()._get_last_sequence_domain(relaxed)
        if self.country_code == "XX" and self.l10n_latam_use_documents:
            where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
            param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
        return where_string, param
```

**Características:**
- ✅ Usan API estándar del `sequence.mixin`
- ✅ Solo sobreescriben `_get_starting_sequence()` y `_get_last_sequence_domain()`
- ✅ No tocan `_set_next_sequence()` ni `_get_last_sequence()`
- ✅ Usan campos estándar: `sequence_prefix`, `sequence_number`

#### **l10n_do_accounting (Implementación Actual)**
```python
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # Campos custom de secuencia
    l10n_do_sequence_prefix = fields.Char(compute="_compute_split_sequence", store=True)
    l10n_do_sequence_number = fields.Integer(compute="_compute_split_sequence", store=True)
    
    # Métodos completamente sobreescritos con SQL raw:
    def _get_last_sequence(self, relaxed=False, with_prefix=None):
        # Implementación custom con SQL directo
        ...
    
    def _set_next_sequence(self):
        # Implementación custom con SQL directo
        ...
```

**Características:**
- 🔴 Implementación completamente custom con SQL raw
- 🔴 Campos de secuencia propios: `l10n_do_sequence_prefix`, `l10n_do_sequence_number`
- 🔴 Sobreescribe `_get_last_sequence()` completamente
- 🔴 Sobreescribe `_set_next_sequence()` completamente

---

## ⚠️ Problemas Potenciales en Odoo 18

### 1. Cambio en API de `flush_model()`

**Odoo 18 - sequence.mixin:**
```python
# Nuevo método preferido en Odoo 18
def _get_last_sequence(self, relaxed=False, with_prefix=None):
    ...
    self.flush_recordset()  # ← Nuevo en Odoo 18
    self.env.cr.execute(query, param)
```

**l10n_do_accounting:**
```python
def _get_last_sequence(self, relaxed=False, with_prefix=None):
    ...
    self.flush_model([...])  # ← Podría no funcionar igual en Odoo 18
```

**Impacto:** El método `flush_model()` con parámetros podría comportarse diferente en Odoo 18.

### 2. Nuevo Mecanismo `_locked_increment()`

**Odoo 18 introdujo:**
```python
def _locked_increment(self, format_string, format_values):
    """Incremento con cache transaccional y locks de base de datos"""
    cache = self._get_sequence_cache()
    ...
```

**Impacto:** l10n_do_accounting no utiliza este mecanismo, lo que puede causar:
- Problemas de concurrencia bajo carga alta
- Posibles duplicados de secuencias
- Inconsistencias en transacciones concurrentes

### 3. Falta de `_sequence_index`

**Odoo 18:**
```python
class SequenceMixin(models.AbstractModel):
    _sequence_index = False  # Atributo de clase importante
```

**l10n_do_accounting:**
- No define `_sequence_index`
- Puede afectar la creación de índices de base de datos para optimizar consultas de secuencia

---

## ✅ Áreas que Funcionan Correctamente

### 1. `_get_starting_sequence()`
**Archivo:** `models/account_move.py:674-681`

El patrón usado es consistente con módulos nativos:
```python
def _get_starting_sequence(self):
    if (
        self.journal_id.l10n_latam_use_documents
        and self.country_code == "DO"
    ):
        return self._l10n_do_get_formatted_sequence()
    return super()._get_starting_sequence()
```

### 2. `_get_last_sequence_domain()`
**Archivo:** `models/account_move.py:683-710`

Similar a l10n_ar y l10n_cl:
```python
def _get_last_sequence_domain(self, relaxed=False):
    where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
    if self.l10n_latam_use_documents and self.country_code == "DO":
        where_string = where_string.replace(...)
        # Filtros por tipo de documento
    return where_string, param
```

### 3. Manejo de Documentos Manuales
**Archivo:** `models/account_move.py:507-526`

El módulo sobreescribe `_is_manual_document_number()` como lo hacen los módulos nativos.

---

## 🔧 Cambios Aplicados durante la Migración

### 1. Método `_post()`
**Archivo:** `models/account_move.py:630-631`

```python
# Cambio realizado:
def _post(self, soft=True):
    res = super(AccountMove, self)._post(soft=soft)  # Llamada explícita a super
```

### 2. Verificación de Recordset Vacío
**Archivo:** `models/account_move.py:307-310`

```python
# Agregado:
def _compute_company_in_contingency(self):
    if not self:
        return  # ← Previene errores en Odoo 18 cuando se computan campos en recordsets vacíos
```

---

## 📋 Recomendaciones para Pruebas

### 1. Probar Concurrencia de Secuencias
```bash
# Ejecutar múltiples procesos simultáneos que creen facturas
# para verificar que no haya duplicados
```

### 2. Verificar Migración de Datos Existentes
```sql
-- Verificar que las secuencias existentes se mantengan correctamente
SELECT l10n_do_sequence_prefix, l10n_do_sequence_number, name 
FROM account_move 
WHERE country_code = 'DO' AND posted_before = True
LIMIT 10;
```

### 3. Validar Formato de NCF
- Verificar que los NCFs nuevos mantienen el formato correcto: `B01XXXXXXXXX` o `E31XXXXXXXXX`
- Validar longitud y estructura

---

## 📊 Comparativa de Métodos Sobreescritos

| Método | l10n_ar | l10n_cl | l10n_do_accounting | Nivel de Riesgo |
|--------|---------|---------|-------------------|-----------------|
| `_get_starting_sequence()` | ✅ | ✅ | ✅ | 🟢 Bajo |
| `_get_last_sequence_domain()` | ✅ | ✅ | ✅ | 🟢 Bajo |
| `_get_last_sequence()` | ❌ No | ❌ No | 🔴 Sí (custom) | 🔴 Alto |
| `_set_next_sequence()` | ❌ No | ❌ No | 🔴 Sí (custom) | 🔴 Alto |
| `_is_manual_document_number()` | ✅ | ✅ | ✅ | 🟢 Bajo |
| `_post()` | ✅ | ✅ | ✅ | 🟢 Bajo |

**Leyenda:**
- ✅ Sobreescrito siguiendo patrón estándar
- ❌ No sobreescrito (usa estándar)
- 🔴 Sobreescrito con implementación custom

---

## 🎯 Conclusión

El módulo `l10n_do_accounting` tiene una implementación de secuencias significativamente más compleja que los módulos nativos. Mientras que `l10n_ar` y `l10n_cl` confían en el `sequence.mixin` estándar de Odoo, `l10n_do_accounting` implementa su propio mecanismo de secuencias con SQL raw.

**Próximos Pasos Sugeridos:**
1. Realizar pruebas exhaustivas de creación de facturas en paralelo
2. Monitorear logs de PostgreSQL para detectar posibles deadlocks
3. Considerar a largo plazo una refactorización para alinearse con el patrón de módulos nativos

---

*Generado el: 2026-05-12*
*Análisis realizado para migración a Odoo 18.0*
