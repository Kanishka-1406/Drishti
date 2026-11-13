function RegionSelector({
  regions,
  selectedRegionId,
  onChange,
}) {
  return (
    <div className="panel">
      <div className="panel-label">
        Region
      </div>

      <select
        value={selectedRegionId ?? ""}
        onChange={(event) =>
          onChange(Number(event.target.value))
        }
      >
        {regions.map((region) => (
          <option
            key={region.id}
            value={region.id}
          >
            {region.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default RegionSelector;